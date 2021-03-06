#!/usr/bin/env python3

# Copyright (c) 2022 Robert Bosch GmbH and Microsoft Corporation
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
import os
import sys

import vspec

from python_generator import VehicleModelPythonGenerator

if __name__ == "__main__":
    # The arguments we accept

    parser = argparse.ArgumentParser(
        description="Convert vspec to Velocitas Vehicle Model code."
    )
    parser.add_argument(
        "-N",
        "--package-name",
        type=str,
        default="vehicle-model",
        help="Name of the module/package.",
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
        default="./vehicle_model",
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
        choices=["python"],
        default="python",
    )
    parser.add_argument(
        "vspec_file",
        metavar="<vspec_file>",
        help="The vehicle specification file to convert.",
    )

    args = parser.parse_args()

    strict = args.strict

    include_dirs = ["."]
    include_dirs.extend(args.include_dir)

    # yaml_out = open(args.yaml_file, "w", encoding="utf-8")

    try:
        print("Loading vspec...")
        tree = vspec.load_tree(
            args.vspec_file,
            include_dirs,
            merge_private=False,
            break_on_noncore_attribute=strict,
            break_on_name_style_violation=strict,
            expand_inst=False,
        )

        if args.language == "python":
            print("Recursing tree and creating Python code...")
            VehicleModelPythonGenerator(
                tree,
                args.target_folder,
                args.package_name,
            ).generate()
            print("All done.")
        else:
            print(f"Language {args.language} is not supported yet.")
    except vspec.VSpecError as e:
        print(f"Error: {e}")
        sys.exit(255)
