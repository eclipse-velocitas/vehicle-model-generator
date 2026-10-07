# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0.
#
# SPDX-License-Identifier: Apache-2.0

import json
import os
import subprocess
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


def install_local_typescript_sdk(project_path: Path, sdk_path: Path) -> None:
    """Install the local SDK and temporarily expose its generic import name."""
    manifest_path = project_path / "package.json"
    original_manifest = manifest_path.read_text(encoding="utf-8")
    manifest = json.loads(original_manifest)
    manifest["dependencies"].pop("vehicle-app-ts-sdk", None)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    try:
        subprocess.check_call(
            ["npm", "install", str(sdk_path), "--no-save", "--no-package-lock"],
            cwd=project_path,
        )
        sdk_manifest = json.loads(
            (sdk_path / "package.json").read_text(encoding="utf-8")
        )
        installed_sdk = project_path / "node_modules" / sdk_manifest["name"]
        generic_import = project_path / "node_modules" / "vehicle-app-ts-sdk"
        if not installed_sdk.exists():
            raise FileNotFoundError(f"Local SDK was not installed at {installed_sdk}")
        if generic_import.resolve() != installed_sdk.resolve():
            if generic_import.is_symlink():
                raise FileExistsError(
                    f"{generic_import} already points to a different SDK installation"
                )
            if generic_import.exists():
                raise FileExistsError(
                    f"Cannot map the local SDK because {generic_import} already exists"
                )
            generic_import.symlink_to(installed_sdk, target_is_directory=True)
    finally:
        manifest_path.write_text(original_manifest, encoding="utf-8")
