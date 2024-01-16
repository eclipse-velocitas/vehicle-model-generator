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
from pathlib import Path
from velocitas.model_generator import generate_model

import pytest
import subprocess
import sys


@pytest.mark.parametrize(
    "language,vss_file", [("python", "vss_rel_3.0.json"), ("cpp", "vss_rel_3.0.json")]
)
def test_generate(language: str, vss_file: str):
    input_file_path = Path(__file__).parent.joinpath(vss_file).__str__()
    generate_model(input_file_path, language, "out", "vehicle")

    if language == "python":
        subprocess.check_call([sys.executable, "-m", "pip", "install", "./out"])
        compileall.compile_dir("./out", force=True)
    elif language == "cpp":
        # TODO: add a check if the package can be installed after generated model is a conan package
        pass
