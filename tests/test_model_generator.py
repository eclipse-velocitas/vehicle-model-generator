# Copyright (c) 2024 Contributors to the Eclipse Foundation
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


@pytest.mark.parametrize("language", ["python", "cpp"])
@pytest.mark.parametrize(
    "input_file_path,include_dir",
    [
        ("json/vss_rel_3.0.json", "."),
        ("vspec/v3.0/spec/VehicleSignalSpecification.vspec", "vspec/v3.0/spec"),
    ],
)
def test_generate(language: str, input_file_path: str, include_dir: str):
    input_file_path = Path(__file__).parent.joinpath("data", input_file_path).__str__()
    generate_model(
        input_file_path, language, "output", "vehicle", include_dir=include_dir
    )

    if language == "python":
        subprocess.check_call([sys.executable, "-m", "pip", "install", "./output"])
        assert compileall.compile_dir("./output", force=True)
    elif language == "cpp":
        subprocess.check_call(["conan", "export", "./output"])
