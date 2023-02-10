#!/usr/bin/env python3

# Copyright (c) 2022-2023 Robert Bosch GmbH and Microsoft Corporation
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

import argparse
import sys

# Until vsspec issue will be fixed: https://github.com/COVESA/vss-tools/issues/208
import vspec  # type: ignore

from sdv.model_generator.cpp.cpp_generator import VehicleModelCppGenerator
from sdv.model_generator.python.python_generator import VehicleModelPythonGenerator
from sdv.model_generator.tree_generator.file_import import FileImport


def main():
    # The arguments we accept

    parser = argparse.ArgumentParser(
        description="Convert vspec to Velocitas Vehicle Model code."
    )
    # Add para to name package
    parser.add_argument(
        "-N",
        "--name",
        type=str,
        default="vehicle",
        help="When generating a python model this is used as name of the module/package.\
             For C++ it is used as root namespace",
    )
    parser.add_argument(
        "-I",
        "--include-dir",
        action="append",
        metavar="dir",
        type=str,
        default=[],
        help="Add include directory to search for included vspec files.",
    )
    parser.add_argument(
        "-T",
        "--target-folder",
        type=str,
        default="./gen_model",
        help="The folder name (with relative path) where the code will be generated.",
    )
    parser.add_argument(
        "-s",
        "--strict",
        action="store_true",
        help="Use strict checking: Terminate when anything not covered"
        " or not recommended by the core VSS specs is found.",
    )
    parser.add_argument(
        "-l",
        "--language",
        help="The target language of the generated code.",
        choices=["python", "cpp"],
        default="python",
    )
    parser.add_argument(
        "-o",
        "--overlays",
        action="append",
        metavar="overlays",
        type=str,
        default=[],
        help="Add overlays that will be layered on top of the VSS file in the order they"
        " appear.",
    )
    parser.add_argument(
        "-e",
        "--extended-attributes",
        type=str,
        default="",
        help="Whitelisted extended attributes as comma separated list. Note, that "
        "extended attributes aren't considered by the generator. This paramter is "
        "only for suppressing warnings/errors.",
    )
    parser.add_argument(
        "import_file_path",
        metavar="<import_file_path>",
        help="The file to convert. Currently supports JSON and Vspec file formats.",
    )

    args = parser.parse_args()

    strict = args.strict

    include_dirs = ["."]
    include_dirs.extend(args.include_dir)

    # yaml_out = open(args.yaml_file, "w", encoding="utf-8")

    ext_attributes_list = args.extended_attributes.split(",")
    if len(ext_attributes_list) > 0:
        vspec.model.vsstree.VSSNode.whitelisted_extended_attributes = (
            ext_attributes_list
        )
        print(f"Known extended attributes: {', '.join(ext_attributes_list)}")

    try:
        tree = FileImport(
            args.import_file_path, include_dirs, strict, args.overlays
        ).load_tree()

        if args.language == "python":
            print("Recursing tree and creating Python code...")
            VehicleModelPythonGenerator(
                tree,
                args.target_folder,
                args.name,
            ).generate()
            print("All done.")
        elif args.language == "cpp":
            print("Recursing tree and creating c++ code...")
            VehicleModelCppGenerator(
                tree,
                args.target_folder,
                args.name,
            ).generate()
            print("All done.")
        else:
            print(f"Language {args.language} is not supported yet.")
    except vspec.VSpecError as e:
        print(f"Error: {e}")
        sys.exit(255)


if __name__ == "__main__":
    main()
