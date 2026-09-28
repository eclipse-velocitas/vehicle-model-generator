# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0.
#
# SPDX-License-Identifier: Apache-2.0

import os
import warnings
from pathlib import Path

import pytest


def require_typescript_sdk_path() -> Path:
    sdk_path = os.environ.get("VEHICLE_APP_TS_SDK_PATH")
    if not sdk_path:
        warnings.warn(
            "TypeScript integration tests require VEHICLE_APP_TS_SDK_PATH; skipping.",
            RuntimeWarning,
            stacklevel=2,
        )
        pytest.skip("VEHICLE_APP_TS_SDK_PATH is not set")

    resolved_path = Path(sdk_path)
    if not resolved_path.is_dir():
        warnings.warn(
            f"TypeScript SDK path does not exist: {resolved_path}; skipping.",
            RuntimeWarning,
            stacklevel=2,
        )
        pytest.skip("VEHICLE_APP_TS_SDK_PATH does not point to a directory")

    return resolved_path
