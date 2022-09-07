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

"""VehicleModelPythonGenerator."""

import os
import re
import shutil
from typing import Set

from vspec.model.vsstree import VSSNode

from utils import CodeGeneratorContext


class VehicleModelPythonGenerator:
    """Generate python code for vehicle model."""

    def __init__(self, root: VSSNode, target_folder: str, package_name: str):
        """Initialize the python generator.

        Args:
            root (_type_): the vspec tree root node.
        """
        self.root = root
        self.target_folder = target_folder
        self.package_name = package_name
        self.ctx = CodeGeneratorContext()
        self.imports: Set[str] = set()
        self.model_imports: Set[str] = set()

    def generate(self):
        """Generate python code for vehicle model."""
        path = self.target_folder

        if os.path.exists(path):
            shutil.rmtree(path)
        os.makedirs(path)

        self.__gen_model(self.root, path, True)
        self.__visit_nodes(self.root, path)

        self.__gen_package()

    def __gen_package(self):
        self.ctx.reset()
        self.ctx.write(
            "from setuptools import find_packages, setup  # type: ignore\n\n"
        )
        self.ctx.write("setup(\n")
        self.ctx.indent()
        self.ctx.write(f'name="{self.package_name}",\n')
        self.ctx.write('version="0.1.0",\n')
        self.ctx.write('description="Vehicle Model",\n')
        self.ctx.write("packages=find_packages(),\n")
        self.ctx.write("zip_safe=False,\n")
        self.ctx.dedent()
        self.ctx.write(")\n")

        path = os.path.dirname(self.target_folder)
        with open(os.path.join(path, "setup.py"), "w", encoding="utf-8") as file:
            file.write(self.ctx.get_content())

    def __visit_nodes(self, node: VSSNode, path: str):
        """Recursively render nodes."""
        # node_path = node.qualified_name()

        for child in node.children:
            child_path = os.path.join(path, child.name)

            if child.type.value == "branch":
                if not os.path.exists(child_path):
                    os.makedirs(child_path)
                self.__gen_model(child, child_path)

                self.__visit_nodes(child, child_path)

    def __gen_header(self, node: VSSNode):
        self.ctx.write(
            f"""#!/usr/bin/env python3

        ""\"{node.name} model.""\"

        # pylint: disable=C0103,R0801,R0902,R0915,C0301,W0235\n\n\n""",
            strip_lines=True,
        )

    def __gen_imports(self):
        self.model_imports.add("Model")
        self.ctx.write("from sdv.model import (\n")
        self.ctx.indent()
        for imp in sorted(self.model_imports):
            self.ctx.write(f"{imp},\n")

        self.ctx.dedent()
        self.ctx.write(")\n\n")

        for imp in sorted(self.imports):
            if imp[0] == ".":
                imp = imp[2:]
            imp = imp.replace("/", ".")
            path = imp.split(".")
            self.ctx.write(f"from {imp} import {path[-1]}\n")

        if len(self.imports) == 0:
            self.ctx.write("\n")
        else:
            self.ctx.write("\n\n")
        self.imports.clear()
        self.model_imports.clear()

    def __gen_model_docstring(self, node: VSSNode):
        self.ctx.write(f'"""{node.name} model.')
        if node.children:
            self.ctx.write("\n\nAttributes\n")
            self.ctx.write("----------\n")
            for i in node.children:
                if i.type.value == "attribute":
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

    def __gen_model(self, node: VSSNode, path: str, is_root=False):
        self.ctx.write(f"class {node.name}(Model):\n")
        self.ctx.indent()

        self.__gen_model_docstring(node)

        if is_root:
            self.ctx.write("def __init__(self):\n")
        else:
            self.ctx.write("def __init__(self, parent):\n")
        self.ctx.indent()
        self.ctx.write(f'"""Create a new {node.name} model."""\n')
        if is_root:
            self.ctx.write("super().__init__()\n")
        else:
            self.ctx.write("super().__init__(parent)\n")

        if node.children:
            self.ctx.write("\n")

        for child in node.children:
            if child.type.value in ("attribute", "sensor", "actuator"):
                self.ctx.write(
                    f"self.{child.name} = DataPoint{self.__get_datatype(child.datatype.value)}"
                    f'("{child.name}", self)\n'
                )
                self.model_imports.add(
                    f"DataPoint{self.__get_datatype(child.datatype.value)}"
                )
            if child.type.value == "branch":
                if child.instances:
                    instances = self.__gen_instances(child)
                    inst_repr = ", ".join(instances)
                    self.ctx.write(
                        f"self.{child.name} = ModelCollection[{child.name}]"
                        f"([{inst_repr}], {child.name}(self))\n"
                    )
                    self.model_imports.add("ModelCollection")
                else:
                    self.ctx.write(f"self.{child.name} = {child.name}(self)\n")
                self.imports.add(f"{path}/{child.name}")

        self.ctx.dedent()
        self.ctx.dedent()

        if is_root:
            self.ctx.write("\n\nvehicle = Vehicle()\n")

        self.ctx.set_position(0)
        self.__gen_header(node)
        self.__gen_imports()

        with open(os.path.join(path, "__init__.py"), "w", encoding="utf-8") as file:
            file.write(self.ctx.get_content())

        self.ctx.reset()

    def __gen_instances(self, node: VSSNode):
        instances = node.instances

        reg_ex = r"\w+\[\d+,(\d+)\]"

        result = []

        complex_list = False
        for i in instances:
            if isinstance(i, list) or re.match(reg_ex, i):
                complex_list = True

        if complex_list:
            for i in instances:
                result.append(self.__parse_instances(reg_ex, i))
        else:
            result.append(self.__parse_instances(reg_ex, instances))

        return result

    def __parse_instances(self, reg_ex, i):

        # parse string instantiation elements (e.g. Row[1,5])
        if isinstance(i, str):
            if re.match(reg_ex, i):
                inst_range_arr = re.split(r"\[+|,+|\]", i)
                range_name = inst_range_arr[0]
                lower_bound = int(inst_range_arr[1])
                upper_bound = int(inst_range_arr[2])
                self.model_imports.add("NamedRange")
                return f'NamedRange("{range_name}", {lower_bound}, {upper_bound})'

            raise ValueError("", "", "instantiation type not supported")

        # Use list elements for instances (e.g. ["LEFT","RIGHT"])
        if isinstance(i, list):
            items = '", "'.join(i)
            self.model_imports.add("Dictionary")
            return f'Dictionary(["{items}"])'

        raise ValueError("", "", f"is of type {type(i)} which is unsupported")

    def __get_datatype(self, datatype):
        if datatype[-1] == "]":
            return datatype[0].upper() + datatype[1:-2] + "Array"
        return datatype[0].upper() + datatype[1:]
