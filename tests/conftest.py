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

import os
import subprocess
from pathlib import Path

from velocitas_lib import download_file


def prepare_vss_repo_data(tag: str, json_path: str) -> None:
    os.makedirs(f"{Path(__file__).parent}/data", exist_ok=True)
    test_data_path = Path(__file__).parent.joinpath("data", "vspec").__str__()
    test_data_json_path = Path(__file__).parent.joinpath("data", "json").__str__()
    tag_short = tag[1:]

    if not os.path.exists(os.path.join(test_data_path, tag)):
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
    if not os.path.isfile(
        os.path.join(test_data_json_path, f"vss_rel_{tag_short}.json")
    ):
        os.makedirs(test_data_json_path, exist_ok=True)
        download_file(
            f"https://github.com/COVESA/vehicle_signal_specification/releases/download/{json_path}",
            f"{test_data_json_path}/vss_rel_{tag_short}.json",
        )


def pytest_configure(config) -> None:
    prepare_vss_repo_data("v3.0", "v3.0/vss_rel_3.0.json")
    prepare_vss_repo_data("v3.1", "v3.1/vss_rel_3.1.json")
    prepare_vss_repo_data("v3.1.1", "v3.1.1/vss_rel_3.1.1.json")
    prepare_vss_repo_data("v4.0", "v4.0/vss_rel_4.0.json")
    prepare_vss_repo_data("v4.1", "v4.1/vss_rel_4.1.json")
    prepare_vss_repo_data("v4.2", "v4.2/vss_rel_4.2.json")
    prepare_vss_repo_data("v5.0", "v5.0/vss.json")
    prepare_vss_repo_data("v5.1", "v5.1/vss.json")
    prepare_vss_repo_data("v6.0", "v6.0/vss.json")
