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

import os
from typing import List

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
        unit_file_path_list: List[str],
        include_dirs: List[str],
        strict: bool,
        overlays: List[str],
    ):
        self.file_path = file_path
        self.include_dirs = include_dirs
        self.strict = strict
        self.overlays = overlays
        # setting the file format implementation object from the file_path
        self.format_implementation = self.__get_format_implementation(
            self.file_path, unit_file_path_list
        )

    def __get_format_implementation(
        self,
        file_path: str,
        unit_file_path_list: List[str],
    ):
        """Initialize implementation of VSPEC or JSON.

        Args:
            file_path str: path to the file that is used for format checking
            unit_file_path_list List[str]: a list of unit files that get checked to be yaml files

        Returns:
            Error UnsupportedFileFormat: If either file specified is not supported.
        """
        file_ext = os.path.splitext(file_path)[1][1:]
        for unit_file_path in unit_file_path_list:
            unit_file_ext = os.path.splitext(unit_file_path)[1][1:]
            if unit_file_ext != "yaml":
                raise UnsupportedFileFormat(unit_file_ext)

        if file_ext in formats:
            if file_ext == VSPEC:
                return Vspec(
                    file_path=self.file_path,
                    unit_file_path_list=unit_file_path_list,
                    include_dirs=self.include_dirs,
                    strict=self.strict,
                    overlays=self.overlays,
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
