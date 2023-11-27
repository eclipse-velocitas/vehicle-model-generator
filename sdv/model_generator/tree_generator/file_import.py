# Copyright (c) 2023 Contributors to the Eclipse Foundation
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

from sdv.model_generator.tree_generator.constants import JSON, VSPEC
from sdv.model_generator.tree_generator.file_formats import Json, Vspec, formats


# if no other file supported format is found
class UnsupportedFileFormat(Exception):
    def __init__(self, format):
        self.format = format
        self.message = f"The {self.format} file format is not supported"
        Exception.__init__(self, self.message)

    def __str__(self):
        return self.message


class FileImport:
    def __init__(self, file_path: str, include_dirs: List, strict, overlays):
        self.file_path = file_path
        self.include_dirs = include_dirs
        self.strict = strict
        self.overlays = overlays
        # setting the file format implementation object from the file_path
        self.format_implementation = self.__get_format_implementation(self.file_path)

    def __get_format_implementation(self, file_path: str):
        file_ext = os.path.splitext(file_path)[1][1:]
        if file_ext in formats:
            if file_ext == VSPEC:
                return Vspec(
                    file_path=self.file_path,
                    include_dirs=self.include_dirs,
                    strict=self.strict,
                    overlays=self.overlays,
                )
            elif file_ext == JSON:
                return Json(file_path=file_path)
        else:
            raise UnsupportedFileFormat(file_ext)

    def load_tree(self):
        return self.format_implementation.load_tree()
