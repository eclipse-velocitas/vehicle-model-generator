# Copyright (c) 2026 Contributors to the Eclipse Foundation
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
import shutil
import tempfile

import pytest

from velocitas.model_generator.typescript.typescript_keywords import (
    is_ts_keyword,
    sanitize_ts_identifier,
)
from velocitas.model_generator.typescript.vss_collection import VssCollection
from velocitas.model_generator.typescript.typescript_generator import (
    VehicleModelTypescriptGenerator,
)
from tests.typescript_sdk import require_typescript_sdk_path
from vss_tools.tree import VSSNode  # type: ignore


def test_missing_typescript_sdk_path_warns_and_skips(monkeypatch):
    monkeypatch.delenv("VEHICLE_APP_TS_SDK_PATH", raising=False)

    with pytest.warns(RuntimeWarning, match="VEHICLE_APP_TS_SDK_PATH"):
        with pytest.raises(pytest.skip.Exception):
            require_typescript_sdk_path()


def test_typescript_keywords_sanitization():
    import pytest

    # Reserved words
    assert is_ts_keyword("class")
    assert is_ts_keyword("function")
    assert is_ts_keyword("default")
    assert is_ts_keyword("delete")
    assert is_ts_keyword("interface")
    assert not is_ts_keyword("Speed")
    assert not is_ts_keyword("Vehicle")

    # Sanitization
    assert sanitize_ts_identifier("class") == "class_"
    assert sanitize_ts_identifier("function") == "function_"
    assert sanitize_ts_identifier("default") == "default_"
    assert sanitize_ts_identifier("name") == "name_"
    assert sanitize_ts_identifier("parent") == "parent_"
    assert sanitize_ts_identifier("Speed") == "Speed"

    # Invalid identifier validation
    with pytest.raises(ValueError, match="not a valid TypeScript identifier"):
        sanitize_ts_identifier("1st")

    with pytest.raises(ValueError, match="not a valid TypeScript identifier"):
        sanitize_ts_identifier("Row[1, 2]")


def test_typescript_vss_collection_simple():
    node = VSSNode(
        name="Seat",
        fqn="Seat",
        data={
            "type": "branch",
            "description": "Seat branch",
            "instances": ["Row[1,2]"],
        },
    )

    collection = VssCollection(node)
    code = collection.ctx.get_content()

    assert "export class SeatCollection extends Branch" in code
    assert "public readonly Row1: Seat;" in code
    assert "public readonly Row2: Seat;" in code
    assert 'this.Row1 = new Seat("Row1", this);' in code
    assert 'this.Row2 = new Seat("Row2", this);' in code
    assert "public row(index: 1 | 2): Seat" in code
    assert "this.#elements[index - 1]" in code
    assert "throw new RangeError(`Index ${index} is out of range [1, 2]`);" in code


def test_typescript_vss_collection_multi_level():
    node = VSSNode(
        name="Seat",
        fqn="Seat",
        data={
            "type": "branch",
            "description": "Seat branch",
            "instances": ["Row[1,2]", ["Left", "Right"]],
        },
    )

    collection = VssCollection(node)
    code = collection.ctx.get_content()

    assert "export class SeatCollection extends Branch" in code
    assert "export class SeatCollection_RowType extends Branch" in code
    assert "public readonly Left: Seat;" in code
    assert "public readonly Right: Seat;" in code
    assert "public readonly Row1: SeatCollection_RowType;" in code
    assert "public readonly Row2: SeatCollection_RowType;" in code
    assert 'this.Row1 = new SeatCollection_RowType("Row1", this);' in code
    assert 'this.Left = new Seat("Left", this);' in code
    assert "public row(index: 1 | 2): SeatCollection_RowType" in code
    assert "public element(index: 1 | 2): Seat" in code


def test_typescript_vss_collection_dimension_limit():
    import pytest

    node = VSSNode(
        name="Seat",
        fqn="Vehicle.Cabin.Seat",
        data={
            "type": "branch",
            "description": "Seat branch",
            "instances": ["Row[1,2]", ["Left", "Right"], ["Front", "Rear"]],
        },
    )

    with pytest.raises(
        ValueError,
        match="Vehicle.Cabin.Seat: instance dimensions > 2 are not supported",
    ):
        VssCollection(node)


def test_typescript_generator_basic():
    root_node = VSSNode(
        name="Vehicle",
        fqn="Vehicle",
        data={"type": "branch", "description": "Vehicle root"},
    )

    speed_node = VSSNode(
        name="Speed",
        fqn="Vehicle.Speed",
        data={"datatype": "float", "type": "sensor", "description": "Vehicle speed"},
    )
    speed_node.parent = root_node
    root_node.children = [speed_node]

    temp_dir = tempfile.mkdtemp()
    try:
        generator = VehicleModelTypescriptGenerator(root_node, temp_dir, "vehicle")
        generator.generate()

        # Check project files
        assert os.path.isfile(os.path.join(temp_dir, "package.json"))
        assert os.path.isfile(os.path.join(temp_dir, "tsconfig.json"))
        assert os.path.isfile(os.path.join(temp_dir, "src", "index.ts"))
        assert not os.path.exists(os.path.join(temp_dir, "src", "sdk"))
        assert os.path.isfile(os.path.join(temp_dir, "src", "vehicle", "Vehicle.ts"))
        assert os.path.isfile(os.path.join(temp_dir, "src", "vehicle", "VehicleFactory.ts"))

        index_ts = open(os.path.join(temp_dir, "src", "index.ts")).read()
        assert 'export type * from "./types.js";' in index_ts
        assert 'export * from "./vehicle/Vehicle.js";' in index_ts
        assert 'export * from "./vehicle/VehicleFactory.js";' in index_ts
        assert 'export * from "vehicle-app-ts-sdk"' not in index_ts

        vehicle_ts = open(os.path.join(temp_dir, "src", "vehicle", "Vehicle.ts")).read()
        assert "export class Vehicle extends Branch" in vehicle_ts
        assert "constructor(client?: VehicleDataBrokerClient) {" in vehicle_ts
        assert 'super("Vehicle", undefined, client);' in vehicle_ts
        assert "public readonly Speed: Sensor<FloatVssType>;" in vehicle_ts
        assert 'this.Speed = new Sensor("Speed", this);' in vehicle_ts
        assert "createVehicle" not in vehicle_ts
        assert "VehicleFactory" not in vehicle_ts
        assert 'import {' in vehicle_ts and '"vehicle-app-ts-sdk"' in vehicle_ts

        factory_ts = open(os.path.join(temp_dir, "src", "vehicle", "VehicleFactory.ts")).read()
        assert "type ModelFactory," in factory_ts
        assert "type VehicleDataBrokerClient," in factory_ts
        assert 'import { Vehicle } from "./Vehicle.js";' in factory_ts
        assert "export class VehicleFactory implements ModelFactory<Vehicle> {" in factory_ts
        assert "create(client?: VehicleDataBrokerClient): Vehicle {" in factory_ts
        assert "return new Vehicle(client);" in factory_ts
    finally:
        shutil.rmtree(temp_dir)


def test_typescript_model_branch_name_no_collision():
    root_node = VSSNode(
        name="Vehicle",
        fqn="Vehicle",
        data={"type": "branch", "description": "Vehicle root"},
    )
    model_node = VSSNode(
        name="Model",
        fqn="Vehicle.Model",
        data={"type": "branch", "description": "Model branch"},
    )
    default_node = VSSNode(
        name="default",
        fqn="Vehicle.Model.default",
        data={"datatype": "uint8", "type": "sensor", "description": "default sensor"},
    )
    default_node.parent = model_node
    model_node.children = [default_node]
    model_node.parent = root_node
    root_node.children = [model_node]

    temp_dir = tempfile.mkdtemp()
    try:
        generator = VehicleModelTypescriptGenerator(root_node, temp_dir, "vehicle")
        generator.generate()

        model_ts = open(os.path.join(temp_dir, "src", "vehicle", "Model", "Model.ts")).read()
        assert "Branch," in model_ts
        assert "export class Model extends Branch" in model_ts
        assert "constructor(name: string, parent?: Node, client?: VehicleDataBrokerClient) {" in model_ts
        assert "super(name, parent, client);" in model_ts
    finally:
        shutil.rmtree(temp_dir)


def test_typescript_same_name_child_branch():
    root_node = VSSNode(
        name="Vehicle",
        fqn="Vehicle",
        data={"type": "branch", "description": "Vehicle root"},
    )
    body1 = VSSNode(
        name="Body",
        fqn="Vehicle.Body",
        data={"type": "branch", "description": "Body root"},
    )
    body2 = VSSNode(
        name="Body",
        fqn="Vehicle.Body.Body",
        data={"type": "branch", "description": "Inner Body"},
    )
    sensor = VSSNode(
        name="IsOpen",
        fqn="Vehicle.Body.Body.IsOpen",
        data={"datatype": "boolean", "type": "sensor", "description": "open sensor"},
    )
    sensor.parent = body2
    body2.children = [sensor]
    body2.parent = body1
    body1.children = [body2]
    body1.parent = root_node
    root_node.children = [body1]

    temp_dir = tempfile.mkdtemp()
    try:
        generator = VehicleModelTypescriptGenerator(root_node, temp_dir, "vehicle")
        generator.generate()

        vehicle_ts = open(os.path.join(temp_dir, "src", "vehicle", "Vehicle.ts")).read()
        assert 'import { Body } from "./Body/Body.js";' in vehicle_ts
        assert "public readonly Body: Body;" in vehicle_ts
        assert 'this.Body = new Body("Body", this);' in vehicle_ts
        assert "Vehicle_Body" not in vehicle_ts

        body_ts = open(os.path.join(temp_dir, "src", "vehicle", "Body", "Body.ts")).read()
        assert "import { Body as Body_Body } from" in body_ts
        assert "public readonly Body: Body_Body;" in body_ts
        assert 'this.Body = new Body_Body("Body", this);' in body_ts
        assert "export class Body extends Branch" in body_ts
        assert "constructor(name: string, parent?: Node, client?: VehicleDataBrokerClient) {" in body_ts
        assert "super(name, parent, client);" in body_ts
    finally:
        shutil.rmtree(temp_dir)


def test_typescript_allowed_and_int64_typing():
    root_node = VSSNode(
        name="Vehicle",
        fqn="Vehicle",
        data={"type": "branch", "description": "Vehicle root"},
    )
    gear_node = VSSNode(
        name="Gear",
        fqn="Vehicle.Gear",
        data={
            "datatype": "string",
            "type": "actuator",
            "allowed": ["P", "R", "N", "D"],
            "description": "Gear actuator",
        },
    )
    big_node = VSSNode(
        name="Big",
        fqn="Vehicle.Big",
        data={
            "datatype": "uint64",
            "type": "sensor",
            "description": "64-bit counter",
        },
    )
    gear_node.parent = root_node
    big_node.parent = root_node
    root_node.children = [gear_node, big_node]

    temp_dir = tempfile.mkdtemp()
    try:
        generator = VehicleModelTypescriptGenerator(root_node, temp_dir, "vehicle")
        generator.generate()

        vehicle_ts = open(os.path.join(temp_dir, "src", "vehicle", "Vehicle.ts")).read()
        assert "public readonly Gear: Actuator<StringVssType>;" in vehicle_ts
        assert "public readonly Big: Sensor<Uint64VssType>;" in vehicle_ts
        assert 'this.Gear = new Actuator("Gear", this, StringVssType);' in vehicle_ts
    finally:
        shutil.rmtree(temp_dir)


def test_typescript_case_collision_detection():
    import pytest

    root_node = VSSNode(
        name="Vehicle",
        fqn="Vehicle",
        data={"type": "branch", "description": "Vehicle root"},
    )
    node1 = VSSNode(
        name="ADAS",
        fqn="Vehicle.ADAS",
        data={"type": "branch", "description": "ADAS branch"},
    )
    node2 = VSSNode(
        name="Adas",
        fqn="Vehicle.Adas",
        data={"type": "branch", "description": "Adas branch"},
    )
    node1.parent = root_node
    node2.parent = root_node
    root_node.children = [node1, node2]

    temp_dir = tempfile.mkdtemp()
    try:
        generator = VehicleModelTypescriptGenerator(root_node, temp_dir, "vehicle")
        with pytest.raises(ValueError, match="Case collision"):
            generator.generate()
    finally:
        shutil.rmtree(temp_dir)


def test_typescript_unsupported_datatype_error():
    import pytest
    from velocitas.model_generator.typescript.typescript_generator import (
        UnsupportedDatatypeError,
    )

    root_node = VSSNode(
        name="Vehicle",
        fqn="Vehicle",
        data={"type": "branch", "description": "Vehicle root"},
    )
    bad_node = VSSNode(
        name="Bad",
        fqn="Vehicle.Bad",
        data={
            "datatype": "Types.MyStruct",
            "type": "sensor",
            "description": "struct ref",
        },
    )
    bad_node.parent = root_node
    root_node.children = [bad_node]

    temp_dir = tempfile.mkdtemp()
    try:
        generator = VehicleModelTypescriptGenerator(root_node, temp_dir, "vehicle")
        with pytest.raises(
            UnsupportedDatatypeError,
            match="Vehicle.Bad: datatype 'Types.MyStruct' is not supported",
        ):
            generator.generate()
    finally:
        shutil.rmtree(temp_dir)


def test_typescript_types_generation():
    root_node = VSSNode(
        name="Vehicle",
        fqn="Vehicle",
        data={"type": "branch", "description": "Vehicle root"},
    )
    body = VSSNode(
        name="Body",
        fqn="Vehicle.Body",
        data={"type": "branch", "description": "Body branch"},
    )
    body.parent = root_node
    root_node.children = [body]

    temp_dir = tempfile.mkdtemp()
    try:
        generator = VehicleModelTypescriptGenerator(root_node, temp_dir, "vehicle")
        generator.generate()

        types_ts_path = os.path.join(temp_dir, "src", "types.ts")
        assert os.path.isfile(types_ts_path)
        types_content = open(types_ts_path).read()
        assert 'export type { Body } from "./vehicle/Body/Body.js";' in types_content
        assert 'export type { Vehicle }' not in types_content
    finally:
        shutil.rmtree(temp_dir)


def test_typescript_tsdoc_formatting():
    root_node = VSSNode(
        name="Vehicle",
        fqn="Vehicle",
        data={"type": "branch", "description": "Vehicle root"},
    )
    speed_node = VSSNode(
        name="Speed",
        fqn="Vehicle.Speed",
        data={
            "datatype": "float",
            "type": "sensor",
            "description": "Vehicle speed.",
            "comment": "Measured in km/h from wheel speed sensors.",
            "unit": "km/h",
            "min": 0,
            "max": 250,
            "deprecation": "Use Vehicle.Speedometer instead.",
        },
    )
    speed_node.parent = root_node
    root_node.children = [speed_node]

    temp_dir = tempfile.mkdtemp()
    try:
        generator = VehicleModelTypescriptGenerator(root_node, temp_dir, "vehicle")
        generator.generate()

        vehicle_ts = open(os.path.join(temp_dir, "src", "vehicle", "Vehicle.ts")).read()
        assert "@deprecated Use Vehicle.Speedometer instead." in vehicle_ts
        assert "Vehicle speed." in vehicle_ts
        assert "@remarks" in vehicle_ts
        assert "Measured in km/h from wheel speed sensors." in vehicle_ts
        assert "Unit: km/h · Range: [0, 250]" in vehicle_ts
        assert "Vehicle root" in vehicle_ts
        assert "@see Vehicle" in vehicle_ts
    finally:
        shutil.rmtree(temp_dir)


def test_typescript_tsc_and_node_smoke():
    import subprocess

    if not shutil.which("npm"):
        pytest.skip("npm is not available")
    sdk_path = require_typescript_sdk_path()

    root_node = VSSNode(
        name="Vehicle",
        fqn="Vehicle",
        data={"type": "branch", "description": "Vehicle root"},
    )
    speed_node = VSSNode(
        name="Speed",
        fqn="Vehicle.Speed",
        data={"datatype": "float", "type": "sensor", "description": "Vehicle speed"},
    )
    speed_node.parent = root_node
    root_node.children = [speed_node]

    temp_dir = tempfile.mkdtemp()
    try:
        generator = VehicleModelTypescriptGenerator(root_node, temp_dir, "vehicle")
        generator.generate()

        res_install = subprocess.run(
            ["npm", "install", str(sdk_path), "--no-package-lock"],
            cwd=temp_dir,
            capture_output=True,
            text=True,
        )
        assert res_install.returncode == 0, res_install.stdout + res_install.stderr

        res_typecheck = subprocess.run(
            ["npx", "tsc", "--project", temp_dir, "--noEmit"],
            cwd=temp_dir,
            capture_output=True,
            text=True,
        )
        assert res_typecheck.returncode == 0, res_typecheck.stdout + res_typecheck.stderr

        res_build = subprocess.run(
            ["npx", "tsc", "--project", temp_dir],
            cwd=temp_dir,
            capture_output=True,
            text=True,
        )
        assert res_build.returncode == 0, res_build.stdout + res_build.stderr

        if shutil.which("node"):
            res_node = subprocess.run(
                [
                    "node",
                    "-e",
                    "import('./dist/index.js').then(m => { "
                    "const mockClient = { getDatapoint: () => {}, setDatapoints: () => {}, subscribe: () => {} }; "
                    "const v = new m.VehicleFactory().create(mockClient); "
                    "if (!v || !v.Speed) throw new Error('Factory create failed'); "
                    "})",
                ],
                cwd=temp_dir,
                capture_output=True,
                text=True,
            )
            assert res_node.returncode == 0, res_node.stdout + res_node.stderr
    finally:
        shutil.rmtree(temp_dir)
