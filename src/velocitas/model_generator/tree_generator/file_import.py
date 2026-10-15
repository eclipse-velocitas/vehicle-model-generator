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

from typing import List
from pathlib import Path

from velocitas.model_generator.tree_generator.constants import JSON, VSPEC
from velocitas.model_generator.tree_generator.file_formats import Json, Vspec, formats


# if no other file supported format is found
class UnsupportedFileFormat(Exception):
    def __init__(self, format):
        self.format = format
        self.message = f"The {self.format} file format is not supported"
        Exception.__init__(self, self.message)

    def __str__(self):
        return self.message


class FileImport:
    def __init__(
        self,
        file_path: str,
        include_dirs: List[str],
        unit_file_path_list: List[str],
        quantity_file_path_list: List[str],
        strict: bool,
        overlays: List[str],
        extended_attributes: List[str],
    ):
        checked_file_path = Path(file_path)
        if not checked_file_path.is_file():
            print(f"Error: File {checked_file_path} does not exist.")
            exit(-1)

        checked_include_dirs = []
        for cur_dir in include_dirs:
            cur_path = Path(cur_dir)
            if not cur_path.is_dir():
                print(f"Warning: Include directory {cur_dir} does not exist.")
            else:
                checked_include_dirs.append(cur_path)

        checked_units_list: list[Path] = []
        if unit_file_path_list:
            for unit_file in unit_file_path_list:
                normalized_path = Path(unit_file)
                if not normalized_path.is_file():
                    print(f"Warning: Unit file {unit_file} does not exist.")
                else:
                    checked_units_list.append(normalized_path)

        checked_quantities_list: list[Path] = []
        for p in quantity_file_path_list:
            for quantity_file in quantity_file_path_list:
                normalized_path = Path(quantity_file)
                if not normalized_path.is_file():
                    print(f"Warning: Quantity file {quantity_file} does not exist.")
                elif normalized_path.suffix != ".yaml":
                    print(f"Warning: Quantity file {quantity_file} is not a yaml file.")
                    raise UnsupportedFileFormat(normalized_path.suffix)
                else:
                    checked_quantities_list.append(normalized_path)

        checked_overlays = []
        if overlays:
            for overlay in [Path(p) for p in overlays]:
                if not overlay.is_file():
                    print(f"Warning: Overlay file {overlay} does not exist.")
                else:
                    print(f"Using overlay file {overlay}")
                    checked_overlays.append(overlay)

        self.file_path = checked_file_path
        self.include_dirs = checked_include_dirs
        self.strict = strict
        self.overlays = checked_overlays
        self.unit_file_path_list = checked_units_list
        self.quantity_file_path_list = checked_quantities_list

        self.extended_attributes = extended_attributes
        # setting the file format implementation object from the file_path
        self.format_implementation = self.__get_format_implementation(
            self.file_path, self.unit_file_path_list, self.quantity_file_path_list
        )

    def __get_format_implementation(
        self,
        file_path: Path,
        unit_file_path_list: List[Path],
        quantity_file_path_list: List[Path],
    ):
        """Initialize implementation of VSPEC or JSON.

        Args:
            file_path Path: path to the file that is used for format checking
            unit_file_path_list List[Path]: a list of unit files that get checked to be yaml files
            quantity_file_path_list List[Path]: a list of quantity files that get checked to be yaml files

        Returns:
            Error UnsupportedFileFormat: If either file specified is not supported.
        """
        file_ext = file_path.suffix[1:]
        if file_ext in formats:
            if file_ext == VSPEC:
                return Vspec(
                    file_path=self.file_path,
                    unit_file_path_list=unit_file_path_list,
                    quantity_file_path_list=quantity_file_path_list,
                    include_dirs=self.include_dirs,
                    strict=self.strict,
                    overlays=self.overlays,
                    extended_attributes=self.extended_attributes,
                )
            elif file_ext == JSON:
                return Json(
                    file_path=file_path,
                    unit_file_path_list=unit_file_path_list,
                )
        else:
            raise UnsupportedFileFormat(file_ext)

    def load_tree(self):
        return self.format_implementation.load_tree()
