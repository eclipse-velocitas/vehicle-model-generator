# Copyright (c) 2022-2024 Contributors to the Eclipse Foundation
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

"""VehicleModelPythonGenerator."""

import os
from typing import List, Set

# Until vsspec issue will be fixed: https://github.com/COVESA/vss-tools/issues/208
from vspec.model.constants import VSSType  # type: ignore
from vspec.model.vsstree import VSSNode  # type: ignore

from velocitas.model_generator.python.vss_collection import VssCollection
from velocitas.model_generator.utils import CodeGeneratorContext


class VehicleModelPythonGenerator:
    """Generate python code for vehicle model."""

    def __init__(self, root_node: VSSNode, target_folder: str, root_package: str):
        """Initialize the python generator.

        Args:
            root (_type_): the vspec tree root node.
        """
        self.root_node = root_node
        self.target_folder = target_folder
        self.ctx = CodeGeneratorContext()
        self.imports: Set[str] = set()
        self.model_imports: Set[str] = set()
        self.collections: List[VssCollection] = []
        if "." in root_package:
            self.root_package_list = root_package.split(".")
        elif "/" in root_package:
            self.root_package_list = root_package.split("/")
        else:
            self.root_package_list = [root_package]

    def generate(self):
        """Generate python code for vehicle model."""
        self.root_path = self.target_folder

        path = os.path.join(self.root_path, *self.root_package_list)
        os.makedirs(path)

        self.__gen_model(self.root_node, self.root_package_list, is_root=True)
        self.__visit_nodes(self.root_node, self.root_package_list)

        self.__gen_package()

    def __gen_package(self):
        self.ctx.reset()
        self.ctx.write(
            "from setuptools import find_packages, setup  # type: ignore\n\n"
        )
        self.ctx.write("setup(\n")
        self.ctx.indent()
        self.ctx.write(f'name="{".".join(self.root_package_list)}",\n')
        self.ctx.write('version="0.1.0",\n')
        self.ctx.write('description="Vehicle Model",\n')
        self.ctx.write("packages=find_packages(),\n")
        self.ctx.write("zip_safe=False,\n")
        self.ctx.dedent()
        self.ctx.write(")\n")

        path = os.path.join(self.target_folder, "setup.py")
        with open(path, "w", encoding="utf-8") as file:
            file.write(self.ctx.get_content())

    def __visit_nodes(self, node: VSSNode, parent_package_list: List[str]):
        """Recursively render nodes."""
        for child in node.children:
            child_package_list = parent_package_list + [child.name]
            child_path = os.path.join(self.root_path, *child_package_list)

            if child.type.value == VSSType.BRANCH.value:
                if not os.path.exists(child_path):
                    os.makedirs(child_path)
                self.__gen_model(child, child_package_list)
                self.__visit_nodes(child, child_package_list)

    def __gen_header(self, node: VSSNode):
        self.ctx.write(
            f"""#!/usr/bin/env python3

        ""\"{node.name} model.""\"

        # pylint: disable=C0103,R0801,R0902,R0915,C0301,W0235\n\n\n""",
            strip_lines=True,
        )

    def __gen_imports(self):
        self.model_imports.add("Model")
        self.ctx.write("from velocitas_sdk.model import (\n")
        self.ctx.indent()
        for imp in sorted(self.model_imports):
            self.ctx.write(f"{imp},\n")

        self.ctx.dedent()
        self.ctx.write(")\n\n")

        for imp in sorted(self.imports):
            if imp[0] == ".":
                imp = imp[2:]
            path = imp.split(".")
            self.ctx.write(f"from {imp} import {path[-1]}\n")

        if len(self.imports) == 0:
            self.ctx.write("\n")
        else:
            self.ctx.write("\n\n")
        self.imports.clear()
        self.model_imports.clear()

    def __write_collections(self):
        for collection in self.collections:
            self.ctx.write(collection.ctx.get_content())
            self.ctx.write(self.ctx.line_break)

        self.collections.clear()

    def __gen_model_docstring(self, node: VSSNode):
        self.ctx.write(f'"""{node.name} model.')
        if node.children:
            self.ctx.write("\n\nAttributes\n")
            self.ctx.write("----------\n")
            for i in node.children:
                if i.type.value == VSSType.ATTRIBUTE.value:
                    self.ctx.write(f"{i.name}: {i.type.value} ({i.datatype.value})\n")
                else:
                    self.ctx.write(f"{i.name}: {i.type.value}\n")

                self.ctx.indent()
                self.ctx.write(f"{i.description}\n")
                self.ctx.write("\n")
                if len(i.comment) > 0:
                    self.ctx.write(f"{i.comment}\n")
                    self.ctx.write("\n")

                if not isinstance(i.min, str) or not isinstance(i.max, str):
                    self.ctx.write(f"Value range: [{i.min}, {i.max}]\n")
                if hasattr(i, "unit"):
                    self.ctx.write(f"Unit: {i.unit}\n")
                if len(i.allowed) > 0:
                    allowed_values = ", ".join(i.allowed)
                    self.ctx.write(f"Allowed values: {allowed_values}\n")
                self.ctx.dedent()
        self.ctx.write('"""\n\n')

    def __gen_model(self, node: VSSNode, package_list: List[str], is_root=False):
        self.ctx.write(f"class {node.name}(Model):\n")
        self.ctx.indent()

        self.__gen_model_docstring(node)

        if is_root:
            self.ctx.write("def __init__(self, name):\n")
        else:
            self.ctx.write("def __init__(self, name, parent):\n")
        self.ctx.indent()
        self.ctx.write(f'"""Create a new {node.name} model."""\n')
        if is_root:
            self.ctx.write("super().__init__()\n")
        else:
            self.ctx.write("super().__init__(parent)\n")

        self.ctx.write("self.name = name\n")

        if node.children:
            self.ctx.write("\n")

        for child in node.children:
            # Check if branch, add class members
            if child.type.value == VSSType.BRANCH.value:
                # if has instances, a collection will be created
                if child.instances:
                    collection = VssCollection(child)
                    self.collections.append(collection)
                    self.ctx.write(
                        f'self.{child.name} = {collection.name}("{child.name}", self)\n'
                    )
                else:
                    # add simple branch member
                    self.ctx.write(
                        f'self.{child.name} = {child.name}("{child.name}", self)\n'
                    )
                self.imports.add(".".join(package_list + [child.name]))
            # else (ATTRIBUTE, SENSOR, ACTUATOR)
            elif child.type.value in (
                VSSType.ATTRIBUTE.value,
                VSSType.SENSOR.value,
                VSSType.ACTUATOR.value,
            ):
                self.ctx.write(
                    f"self.{child.name} = "
                    f"DataPoint{self.__get_datatype(child.datatype.value)}"
                    f'("{child.name}", self)\n'
                )
                self.model_imports.add(
                    f"DataPoint{self.__get_datatype(child.datatype.value)}"
                )

        self.ctx.dedent()
        self.ctx.dedent()

        self.__write_collections()

        if is_root:
            self.ctx.write('\n\nvehicle = Vehicle("Vehicle")\n')

        self.ctx.set_position(0)
        self.__gen_header(node)
        self.__gen_imports()

        path = os.path.join(self.root_path, *package_list)
        with open(os.path.join(path, "__init__.py"), "w", encoding="utf-8") as file:
            file.write(self.ctx.get_content())

        self.ctx.reset()

    def __get_datatype(self, datatype):
        if datatype[-1] == "]":
            return datatype[0].upper() + datatype[1:-2] + "Array"
        return datatype[0].upper() + datatype[1:]
