# Copyright (c) 2023 Robert Bosch GmbH
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

import re
from typing import List
from sdv.model_generator.tree_generator.file_formats import formats, Json, Vspec
from sdv.model_generator.tree_generator.constants import VSPEC, JSON


# if no other file supported format is found
class UnsupportedFileFormat(Exception):
    def __init__(self, *args, **kwargs):
        self.file_name = args[0]
        self.line_nr = args[1]
        self.message = args[2]
        Exception.__init__(self, *args, **kwargs)

    def __str__(self):
        return "{}: {}: {}".format(self.file_name, self.line_nr, self.message)


class FileImport:

    def __init__(self, file_path: str, include_dirs: List, strict, overlays):
        self.file_path = file_path
        self.include_dirs = include_dirs
        self.strict = strict
        self.overlays = overlays
        # setting the format from the file_path
        self.file_format = self.__get_format(self.file_path)

    def __get_format(self, file_path: str):
        for format in formats:
            if re.match(r"^.+\." + f"{format}" + r"$", file_path):
                if format == VSPEC:
                    return Vspec(file_path=self.file_path,
                                 include_dirs=self.include_dirs,
                                 strict=self.strict,
                                 overlays=self.overlays)
                elif format == JSON:
                    return Json(file_path=file_path)
        raise UnsupportedFileFormat(self.file_path,
                                    0,
                                    "Input file format is not supported")

    def load_tree(self):
        return self.file_format.load_tree()

