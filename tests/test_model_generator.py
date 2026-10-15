# Copyright (c) 2024-2026 Contributors to the Eclipse Foundation
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

import compileall
import subprocess
import sys
from pathlib import Path

import pytest
from velocitas.model_generator import generate_model

test_data_base_path = Path(__file__).parent.joinpath("data")


def get_unit_file_paths(input_file_path: str, include_dir: str) -> list[str]:
    include_path = test_data_base_path.joinpath(include_dir)
    if (
        input_file_path.endswith(".vspec")
        and include_path.joinpath("units.yaml").is_file()
    ):
        return [include_path.joinpath("units.yaml").__str__()]

    return [test_data_base_path.joinpath("units.yaml").__str__()]


@pytest.mark.parametrize("language", ["python", "cpp"])
@pytest.mark.parametrize(
    "input_file_path,include_dir,out_dir",
    [
        ("json/vss_rel_3.0.json", ".", "output/json/vss3.0"),
        ("json/vss_rel_3.1.json", ".", "output/json/vss3.1"),
        ("json/vss_rel_3.1.1.json", ".", "output/json/vss3.1.1"),
        ("json/vss_rel_4.0.json", ".", "output/json/vss4.0"),
        ("json/vss_rel_4.1.json", ".", "output/json/vss4.1"),
        ("json/vss_rel_4.2.json", ".", "output/json/vss4.2"),
        ("json/vss_rel_5.0.json", ".", "output/json/vss5.0"),
        ("json/vss_rel_5.1.json", ".", "output/json/vss5.1"),
        ("json/vss_rel_6.0.json", ".", "output/json/vss6.0"),
        # because of typo in the specifications 3.0, 3.1, 3.11, 4.0, 4,1, 4.2 and 5.1 are not supported
        # ("vspec/v3.0/spec/VehicleSignalSpecification.vspec", "vspec/v3.0/spec", "output/vspec/v3.0"),
        # ("vspec/v3.1/spec/VehicleSignalSpecification.vspec", "vspec/v3.1/spec", "output/vspec/v3.1"),
        # ("vspec/v3.1.1/spec/VehicleSignalSpecification.vspec", "vspec/v3.1.1/spec", "output/vspec/v3.1.1"),
        # ("vspec/v4.0/spec/VehicleSignalSpecification.vspec","vspec/v4.0/spec","output/vspec/v4.0",),
        # ("vspec/v4.1/spec/VehicleSignalSpecification.vspec", "vspec/v4.1/spec", "output/vspec/v4.1"),
        #  ("vspec/v4.2/spec/VehicleSignalSpecification.vspec", "vspec/v4.2/spec", "output/vspec/v4.2"),
        (
            "vspec/v5.0/spec/VehicleSignalSpecification.vspec",
            "vspec/v5.0/spec",
            "output/vspec/v5.0",
        ),
        # ("vspec/v5.1/spec/VehicleSignalSpecification.vspec", "vspec/v5.1/spec", "output/vspec/v5.1"),
        (
            "vspec/v6.0/spec/VehicleSignalSpecification.vspec",
            "vspec/v6.0/spec",
            "output/vspec/v6.0",
        ),
    ],
)
def test_generate(
    language: str, input_file_path: str, include_dir: str, out_dir: str
) -> None:
    input_file_path = Path(__file__).parent.joinpath("data", input_file_path).__str__()
    input_unit_file_path_list = get_unit_file_paths(input_file_path, include_dir)
    output_path = Path(__file__).parent.joinpath(out_dir).joinpath(language).__str__()
    print(input_unit_file_path_list)
    print(output_path)
    generate_model(
        input_file_path,
        input_unit_file_path_list,
        [],
        language,
        output_path,
        "vehicle",
        include_dir=[include_dir],
    )

    if language == "python":
        subprocess.check_call([sys.executable, "-m", "pip", "install", output_path])
        assert compileall.compile_dir(output_path, force=True)
    elif language == "cpp":
        subprocess.check_call(["conan", "export", output_path])
