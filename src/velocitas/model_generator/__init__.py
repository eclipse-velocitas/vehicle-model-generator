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

#!/usr/bin/env python3

# Copyright (c) 2022-2024 Contributors to the Eclipse Foundation
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

"""Convert all vspec input files to Velocitas Python Vehicle Model."""

import os
import shutil
import sys
from typing import List

import vspec  # type: ignore

from velocitas.model_generator.cpp.cpp_generator import VehicleModelCppGenerator
from velocitas.model_generator.python.python_generator import (
    VehicleModelPythonGenerator,
)
from velocitas.model_generator.tree_generator.file_import import (
    FileImport,
    UnsupportedFileFormat,
)


def generate_model(
    input_file_path: str,
    input_unit_file_path_list: List[str],
    language: str,
    target_folder: str = "./gen_model",
    name: str = "vehicle",
    strict: bool = True,
    include_dir: str = ".",
    ext_attributes_list: List[str] = [],
    overlays: List[str] = [],
) -> None:
    """Generates a model to a file (json, vspec)
    input_file_path str: The file to convert.
    input_unit_file_path_list List[str]: The unit file(s) used to generate the model.
    language str: The programming language used (python/cpp).
    target_folder str: The folder where the model should be generated to.
    name str: The name of the model
    strict bool: If enabled checks for VSS terminoligy.
    include_dir: which directories to include for file searches
    ext_attributes_list List[str]: The extended attributes that aren't considered by the generator (no warnings)
    overlays List[str]: The overlay that is used to generate the model.
    """

    include_dirs = ["."]
    include_dirs.extend(include_dir)

    # yaml_out = open(args.yaml_file, "w", encoding="utf-8")

    if len(ext_attributes_list) > 0:
        vspec.model.vsstree.VSSNode.whitelisted_extended_attributes = (
            ext_attributes_list
        )
        print(f"Known extended attributes: {', '.join(ext_attributes_list)}")

    try:
        if os.path.exists(target_folder):
            shutil.rmtree(target_folder)

        tree = FileImport(
            input_file_path,
            input_unit_file_path_list,
            include_dirs,
            strict,
            overlays,
        ).load_tree()

        if language == "python":
            print("Recursing tree and creating Python code...")
            VehicleModelPythonGenerator(
                tree,
                target_folder,
                name,
            ).generate()
            print("All done.")
        elif language == "cpp":
            print("Recursing tree and creating c++ code...")
            VehicleModelCppGenerator(
                tree,
                target_folder,
                name,
            ).generate()
            print("All done.")
        else:
            print(f"Language {language} is not supported yet.")
    except vspec.VSpecError as e:
        print(f"Error: {e}")
        sys.exit(255)
    except UnsupportedFileFormat as e:
        print(f"Error: {e}")
        sys.exit(255)
