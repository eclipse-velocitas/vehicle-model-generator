# Copyright (c) 2023-2026 Contributors to the Eclipse Foundation
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0

import json
import tempfile
from abc import abstractmethod
from typing import Any, List, TypedDict, cast
from pathlib import Path
from sys import exit

from vss_tools.main import get_trees
from vss_tools.tree import VSSNode  # type: ignore
import yaml  # type: ignore

from velocitas.model_generator.tree_generator.constants import JSON, VSPEC

# supported file formats
formats = [VSPEC, JSON]

# TypedDict describing a normalized unit entry (allows the hyphen-key via functional form)
UnitEntry = TypedDict(
    "UnitEntry",
    {
        "definition": str,
        "unit": str,
        "quantity": str,
        "allowed-datatypes": List[str],
    },
)


def _normalize_legacy_unit_content(content: dict[str, Any]) -> dict[str, UnitEntry]:
    # Unit file syntax changed in VSS 4.1. For details, see
    # https://github.com/COVESA/vehicle_signal_specification/blob/release/4.2/CHANGELOG.md#vss-41
    units = content.get("units")
    if not isinstance(units, dict):
        return cast(dict[str, UnitEntry], content)

    reference_units: dict[str, UnitEntry] = {}
    normalized_units: dict[str, UnitEntry] = {}
    for unit_name, unit_data in units.items():
        reference_unit = reference_units.get(unit_name)
        if isinstance(reference_unit, dict):
            normalized_units[unit_name] = cast(UnitEntry, dict(reference_unit))
            continue

        if not isinstance(unit_data, dict):
            normalized_units[unit_name] = {
                "definition": str(unit_data),
                "unit": unit_name,
                "quantity": unit_name,
                "allowed-datatypes": ["numeric"],
            }
            continue

        normalized_units[unit_name] = {
            "definition": str(
                unit_data.get("description") or unit_data.get("label") or unit_name
            ),
            "unit": unit_name,
            "quantity": str(
                unit_data.get("quantity") or unit_data.get("domain") or unit_name
            ),
            "allowed-datatypes": ["numeric"],
        }

    return normalized_units


def _extract_legacy_quantities(
    normalized_units: dict[str, UnitEntry],
) -> dict[str, Any]:
    # Generate quantities.yaml content from legacy unit file content.
    # This is needed for VSS 4.1 and 4.2, which do not have a quantities.yaml file.
    if not isinstance(normalized_units, dict):
        return {}

    quantities: dict[str, dict[str, str]] = {}
    for unit_data in normalized_units.values():
        if not isinstance(unit_data, dict):
            continue

        quantity_name = str(unit_data.get("quantity") or "unknown")
        if quantity_name not in quantities:
            quantities[quantity_name] = {"definition": quantity_name}

    return quantities


class FileFormat:
    def __init__(self, file_path: Path):
        self.file_path = file_path

    # method to override when adding a new format
    @abstractmethod
    def load_tree(self):
        pass


class Vspec(FileFormat):
    def __init__(
        self,
        file_path: Path,
        unit_file_path_list: List[Path],
        quantity_file_path_list: List[Path],
        include_dirs: List[Path],
        strict: bool,
        overlays: List[Path],
        extended_attributes: List[str],
    ):
        super().__init__(file_path)
        self.unit_file_path_list = unit_file_path_list
        self.quantity_file_path_list = quantity_file_path_list
        self.include_dirs = include_dirs
        self.strict = strict
        self.overlays = overlays
        self.extended_attributes = extended_attributes

    def load_tree(self):
        """loads a tree of a vspec file through vss-tools"""
        print("Loading vspec...")

        with tempfile.TemporaryDirectory() as temp_dir:
            unit_file_path_list = []
            generated_quantities_path = None

            # check for units.yaml in old format and units.yaml and quantities.yaml in new format if needed
            for source_path in self.unit_file_path_list:
                content = yaml.safe_load(source_path.read_text())
                if isinstance(content, dict) and "units" in content:
                    normalized_content = _normalize_legacy_unit_content(content)
                    normalized_path = Path(temp_dir) / source_path.name
                    normalized_path.write_text(
                        yaml.safe_dump(normalized_content),
                        encoding="utf-8",
                    )
                    unit_file_path_list.append(normalized_path)

                    legacy_quantities = _extract_legacy_quantities(normalized_content)
                    if legacy_quantities and not self.quantity_file_path_list:
                        generated_quantities_path = Path(temp_dir) / "quantities.yaml"
                        generated_quantities_path.write_text(
                            yaml.safe_dump(legacy_quantities),
                            encoding="utf-8",
                        )
                        self.quantity_file_path_list.append(generated_quantities_path)
                else:
                    unit_file_path_list.append(source_path)

            (tree, tree_types) = get_trees(
                self.file_path,
                self.include_dirs,
                quantities=self.quantity_file_path_list,
                units=self.unit_file_path_list,
                overlays=self.overlays,
                strict=self.strict,
                extended_attributes=self.extended_attributes,
                expand=False,
            )

        return tree


class Json(FileFormat):
    def __init__(self, file_path: Path, unit_file_path_list: List[Path]):
        super().__init__(file_path)
        self.unit_file_path_list = unit_file_path_list

    # VSS nodes have a field "$file_name",
    # so it needs to be added for the vss-tools to work
    def __extend_fields(self, d: dict):
        if "children" in d:
            for child_d in d["children"].values():
                self.__extend_fields(child_d)
        d["$file_name$"] = ""
        return

    def __render_data(self, json_keys):
        data = {}
        for key in json_keys.keys():
            if key != "children":
                data[key] = json_keys[key]
        return data

    def __render_subtree(self, subtree, parent):
        for element_name in subtree:
            current_element = subtree[element_name]

            element_data = self.__render_data(current_element)
            try:
                new_element = VSSNode(element_name, None, element_data)
                new_element.parent = parent
            except Exception as e:
                print(f"Invalid VSS: {e}")
                print("Terminating.")
                exit(-1)
            if "children" in current_element.keys():
                child_nodes = current_element["children"]

                self.__render_subtree(child_nodes, new_element)

    def __render_tree(self, tree_dict) -> VSSNode:
        if len(tree_dict) != 1:
            for item in tree_dict.keys():
                print(f"Found root node {item}")
            raise Exception(
                f"Invalid VSS model, must have single root node, found {len(tree_dict)}"
            )

        root_element_name = next(iter(tree_dict.keys()))
        root_element = tree_dict[root_element_name]

        root_data = self.__render_data(root_element)

        tree_root = VSSNode(
            root_element_name, root_element_name, root_data, parent=None
        )

        if "children" in root_element.keys():
            child_nodes = root_element["children"]
            self.__render_subtree(child_nodes, tree_root)

        return tree_root

    def load_tree(self):
        """loads a tree of a json file through vss-tools"""
        print("Loading json...")
        output_json = json.load(open(self.file_path))
        self.__extend_fields(next(iter(output_json.values())))
        print("Generating tree from json...")

        tree = self.__render_tree(output_json)
        return tree
