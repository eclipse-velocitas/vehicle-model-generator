#!/usr/bin/env python3

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

import re
from typing import List

# Until vsspec issue will be fixed: https://github.com/COVESA/vss-tools/issues/208
from vspec.model.vsstree import VSSNode  # type: ignore

from velocitas.model_generator.utils import CodeGeneratorContext

_COLLECTION_SUFFIX = "Collection"
_COLLECTION_REG_EX = r"\w+\[\d+,(\d+)\]"

_TYPE_SUFFIX = "Type"
_DEFAULT_RANGE_NAME = "element"

"""VSS Collection helper."""


class VssInstance:
    """VSS Instance Model."""

    def __init__(self, name: str, content: List[str], is_range: bool):
        """Construct of new insntance object."""
        # Content List
        self.content = content

        # The name of the Instance
        self.name = name

        # Is a named range flag that will be used to generate
        # getter function for element by index.
        self.is_range = is_range


class VssCollection:
    """VSS Collection Object."""

    def __init__(self, node: VSSNode):
        """Construct of new collection object."""
        self.ctx = CodeGeneratorContext()
        self.name = f"{node.name}{_COLLECTION_SUFFIX}"
        self.__gen_collection(node)

    def __gen_collection(self, node: VSSNode):
        print(f"- {self.name:30}{node.instances}")
        self.ctx.write(self.ctx.line_break)
        self.ctx.write(f"class {self.name}(Model):\n")
        with self.ctx as def_ctx:
            def_ctx.write("def __init__(self, name, parent):\n")
            with def_ctx as body_ctx:
                body_ctx.write("super().__init__(parent)\n")
                body_ctx.write("self.name = name\n")

                complex_list = False
                for instance in node.instances:
                    if isinstance(instance, list) or re.match(
                        _COLLECTION_REG_EX, instance
                    ):
                        complex_list = True

                vss_instance = None
                instance_list_len = len(node.instances)
                instance_type = f"{node.name}"
                has_inner_types = False
                if complex_list:
                    # Complex Instances collection
                    vss_instance = self.__parse_instances(
                        _COLLECTION_REG_EX, node.instances[0]
                    )

                    # if instance_list_len = 1:
                    #   -> Flat instance type (list of single instance type).
                    # # E.g ['Sensor[1,8]']
                    # if instance_list_len > 1
                    #   -> Multi-level (nested) instance type.
                    # E.g ['Row[1,2]', ['Left', 'Right']]
                    if instance_list_len > 1:
                        instance_type = f"{vss_instance.name}{_TYPE_SUFFIX}"
                        has_inner_types = True

                else:
                    # Simple instance type (list object).
                    # E.g. Row[1,4] or ['Low', 'High']
                    vss_instance = self.__parse_instances(
                        _COLLECTION_REG_EX, node.instances
                    )

                instance_list = vss_instance.content

                # check if self needs to be added due to the internal type.
                prefix = "self." if has_inner_types else ""
                for inst in instance_list:
                    body_ctx.write(
                        f'self.{inst} = {prefix}{instance_type}("{inst}", self)\n'
                    )

        with self.ctx as getter_ctx:
            # add getter
            self.__gen_getter(vss_instance.name, instance_list, getter_ctx)

        # Parse inner types
        if has_inner_types:
            self.ctx.write(self.ctx.line_break)
            # add inner types
            inner_instances = self.__parse_instances(
                _COLLECTION_REG_EX, node.instances[1]
            )
            self.__gen_collection_types(node.name, instance_type, inner_instances)
            # add getter
            self.ctx.indent()
            with self.ctx as getter_ctx:
                if inner_instances.is_range:
                    self.__gen_getter(
                        inner_instances.name, inner_instances.content, getter_ctx
                    )
                else:
                    self.__gen_getter(
                        _DEFAULT_RANGE_NAME, inner_instances.content, getter_ctx
                    )

    def __gen_collection_types(self, name, type_name, vss_instance: VssInstance):
        print(f"{' ' * 5}- {type_name:25}{vss_instance.content}")
        with self.ctx as type_ctx:
            type_ctx.write(self.ctx.line_break)
            type_ctx.write(f"class {type_name}(Model):\n")
            with type_ctx as def_ctx:
                def_ctx.write("def __init__(self, name, parent):\n")
                with def_ctx as body_ctx:
                    body_ctx.write("super().__init__(parent)\n")
                    body_ctx.write("self.name = name\n")

                    for instance in vss_instance.content:
                        body_ctx.write(
                            f'self.{instance} = {name}("{instance}", self)\n'
                        )

    def __gen_getter(self, name, instances, base_ctx):
        count = len(instances)
        base_ctx.write(base_ctx.line_break)
        base_ctx.write(f"def {name}(self, index: int):\n")
        with base_ctx as body_ctx:
            body_ctx.write(f"if index < 1 or index > {count}:\n")
            body_ctx.indent()
            body_ctx.write(
                f'raise IndexError(f"Index {{index}} is out of range [1, {count}]")\n'
            )
            body_ctx.dedent()
            body_ctx.write("_options = {\n")
            body_ctx.indent()

            for index in range(len(instances)):
                base_ctx.write(f"{index + 1}: self.{instances[index]},\n")

            body_ctx.dedent()
            body_ctx.write("}\n")
            body_ctx.write("return _options.get(index)")

    def __parse_instances(self, reg_ex, instance) -> VssInstance:
        result = []

        # parse string instantiation elements (e.g. Row[1,5])
        range_name = _DEFAULT_RANGE_NAME
        if isinstance(instance, str):
            if re.match(reg_ex, instance):
                inst_range_arr = re.split(r"\[+|,+|\]", instance)
                range_name = inst_range_arr[0]
                lower_bound = int(inst_range_arr[1])
                upper_bound = int(inst_range_arr[2])
                for element in range(lower_bound, upper_bound + 1):
                    result.append(f"{range_name}{element}")

                return VssInstance(range_name, result, True)

            raise ValueError("", "", f"instantiation type {instance} not supported")

        # Use list elements for instances (e.g. ["LEFT","RIGHT"])
        if isinstance(instance, list):
            for element in instance:
                result.append(f"{element}")
            return VssInstance(range_name, result, False)

        raise ValueError("", "", f"is of type {type(instance)} which is unsupported")
