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

import os
import subprocess
from pathlib import Path


def prepare_vss_repo_data(tag: str) -> None:
    test_data_path = Path(__file__).parent.joinpath("data", "vspec").__str__()
    if os.path.exists(os.path.join(test_data_path, tag)):
        return

    os.makedirs(test_data_path, exist_ok=True)

    subprocess.call(
        [
            "git",
            "clone",
            "-b",
            tag,
            "https://github.com/COVESA/vehicle_signal_specification.git",
            tag,
        ],
        cwd=test_data_path,
    )


def pytest_configure(config) -> None:
    prepare_vss_repo_data("v3.0")
    prepare_vss_repo_data("v4.0")
