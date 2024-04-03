# Copyright (c) 2023-2024 Contributors to the Eclipse Foundation
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
from abc import abstractmethod
from typing import List

import vspec  # type: ignore

from velocitas.model_generator.tree_generator.constants import JSON, VSPEC

# supported file formats
formats = [VSPEC, JSON]


class FileFormat:
    def __init__(self, file_path: str):
        self.file_path = file_path

    # method to override when adding a new format
    @abstractmethod
    def load_tree(self):
        pass


class Vspec(FileFormat):
    def __init__(
        self,
        file_path: str,
        unit_file_path_list: List[str],
        include_dirs: List,
        strict: bool,
        overlays: List[str],
    ):
        super().__init__(file_path)
        self.unit_file_path_list = unit_file_path_list
        self.include_dirs = include_dirs
        self.strict = strict
        self.overlays = overlays

    def load_tree(self):
        """loads a tree of a vspec file through vss-tools"""
        print("Loading vspec...")
        vspec.load_units(
            self.file_path,
            self.unit_file_path_list,
        )
        tree = vspec.load_tree(
            self.file_path,
            self.include_dirs,
            tree_type=vspec.VSSTreeType.SIGNAL_TREE,
            break_on_name_style_violation=self.strict,
            expand_inst=False,
        )

        for overlay in self.overlays:
            print(f"Applying VSS overlay from {overlay}...")
            overlay_tree = vspec.load_tree(
                overlay,
                self.include_dirs,
                merge_private=False,
                break_on_unknown_attribute=self.strict,
                break_on_name_style_violation=self.strict,
                expand_inst=False,
            )
            vspec.merge_tree(tree, overlay_tree)
        return tree


class Json(FileFormat):
    def __init__(self, file_path: str, unit_file_path_list: List[str]):
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

    def load_tree(self):
        """loads a tree of a json file through vss-tools"""
        print("Loading json...")
        output_json = json.load(open(self.file_path))
        self.__extend_fields(next(iter(output_json.values())))
        print("Generating tree from json...")
        vspec.load_units(
            self.file_path,
            self.unit_file_path_list,
        )
        tree = vspec.render_tree(output_json, vspec.VSSTreeType.SIGNAL_TREE)
        return tree
