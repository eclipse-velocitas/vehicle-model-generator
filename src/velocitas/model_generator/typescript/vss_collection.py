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

"""VSS Collection helper for TypeScript."""

import re
from typing import List, cast

from vss_tools.tree import VSSNode, VSSDataBranch  # type: ignore

from velocitas.model_generator.typescript.typescript_keywords import (
    sanitize_ts_identifier,
)
from velocitas.model_generator.utils import CodeGeneratorContext

_COLLECTION_SUFFIX = "Collection"
_COLLECTION_REG_EX = r"\w+\[\s*\d+\s*,\s*\d+\s*\]"
_TYPE_SUFFIX = "Type"
_DEFAULT_RANGE_NAME = "element"


class VssInstance:
    """VSS Instance Model."""

    def __init__(self, name: str, content: List[str], is_range: bool):
        self.content = content
        self.name = name
        self.is_range = is_range


class VssCollection:
    """VSS Collection Generator for TypeScript."""

    def __init__(self, node: VSSNode, element_type: str | None = None):
        self.ctx = CodeGeneratorContext()
        self.name = f"{node.name}{_COLLECTION_SUFFIX}"
        self.node_name = node.name
        self.element_type = element_type or node.name
        self._gen_collection(node)

    def _gen_collection(self, node: VSSNode):
        node_data = cast(VSSDataBranch, node.data)
        if node_data.instances is None:
            fqn = getattr(node.data, "fqn", node.name)
            raise ValueError(
                f"{fqn}: instances attribute is required for collection node"
            )

        complex_list = False
        for instance in node_data.instances:
            if isinstance(instance, list) or re.match(_COLLECTION_REG_EX, instance):
                complex_list = True

        instance_list_len = len(node_data.instances)
        has_inner_types = False
        inner_instances = None
        inner_type_name = f"{self.name}_{node.name}{_TYPE_SUFFIX}"

        if complex_list:
            if instance_list_len > 2:
                fqn = getattr(node.data, "fqn", node.name)
                raise ValueError(
                    f"{fqn}: instance dimensions > 2 are not supported by the TypeScript generator"
                )
            vss_instance = self._parse_instances(
                _COLLECTION_REG_EX, node_data.instances[0]
            )
            if instance_list_len > 1:
                inner_type_name = f"{self.name}_{vss_instance.name}{_TYPE_SUFFIX}"
                has_inner_types = True
                inner_instances = self._parse_instances(
                    _COLLECTION_REG_EX, node_data.instances[1]
                )
        else:
            vss_instance = self._parse_instances(
                _COLLECTION_REG_EX, node_data.instances
            )

        self.has_inner_types = has_inner_types
        self.inner_type_name = inner_type_name

        # Generate inner type class first if multi-level
        if has_inner_types and inner_instances:
            self._gen_inner_type_class(self.element_type, inner_type_name, inner_instances)

        # Generate main collection class
        instance_type = inner_type_name if has_inner_types else self.element_type
        instance_list = vss_instance.content

        self.ctx.write(f"export class {self.name} extends Branch {{\n")
        self.ctx.indent()

        # Members declaration
        for inst in instance_list:
            prop_name = sanitize_ts_identifier(inst)
            self.ctx.write(f"public readonly {prop_name}: {instance_type};\n")

        self.ctx.write(f"readonly #elements: readonly {instance_type}[];\n\n")

        # Constructor
        self.ctx.write(
            "constructor(parent?: Node, client?: VehicleDataBrokerClient) {\n"
        )
        self.ctx.indent()
        self.ctx.write(f'super("{node.name}", parent, client);\n\n')
        for inst in instance_list:
            prop_name = sanitize_ts_identifier(inst)
            self.ctx.write(
                f'this.{prop_name} = new {instance_type}("{inst}", this);\n'
            )
        elements_init = ", ".join(
            f"this.{sanitize_ts_identifier(inst)}" for inst in instance_list
        )
        self.ctx.write(f"this.#elements = [{elements_init}];\n")
        self.ctx.dedent()
        self.ctx.write("}\n\n")

        # Getter method
        self._gen_getter(vss_instance.name, instance_list, instance_type)

        self.ctx.dedent()
        self.ctx.write("}\n\n")

    def _gen_inner_type_class(
        self, element_type: str, type_name: str, inner_instances: VssInstance
    ):
        self.ctx.write(f"export class {type_name} extends Branch {{\n")
        self.ctx.indent()

        for inst in inner_instances.content:
            prop_name = sanitize_ts_identifier(inst)
            self.ctx.write(f"public readonly {prop_name}: {element_type};\n")

        self.ctx.write(f"readonly #elements: readonly {element_type}[];\n\n")

        self.ctx.write(
            "constructor(name: string, parent?: Node, client?: VehicleDataBrokerClient) {\n"
        )
        self.ctx.indent()
        self.ctx.write("super(name, parent, client);\n\n")
        for inst in inner_instances.content:
            prop_name = sanitize_ts_identifier(inst)
            self.ctx.write(f'this.{prop_name} = new {element_type}("{inst}", this);\n')
        inner_elements_init = ", ".join(
            f"this.{sanitize_ts_identifier(inst)}" for inst in inner_instances.content
        )
        self.ctx.write(f"this.#elements = [{inner_elements_init}];\n")
        self.ctx.dedent()
        self.ctx.write("}\n")

        if inner_instances.is_range:
            self.ctx.write("\n")
            self._gen_getter(
                inner_instances.name, inner_instances.content, element_type
            )
        elif len(inner_instances.content) > 0:
            self.ctx.write("\n")
            self._gen_getter(
                _DEFAULT_RANGE_NAME, inner_instances.content, element_type
            )

        self.ctx.dedent()
        self.ctx.write("}\n\n")

    def _gen_getter(self, getter_name: str, instances: List[str], return_type: str):
        count = len(instances)
        camel_getter = (
            getter_name[0].lower() + getter_name[1:]
            if getter_name
            else _DEFAULT_RANGE_NAME
        )
        sanitized_getter = sanitize_ts_identifier(camel_getter)
        index_type = (
            " | ".join(str(i + 1) for i in range(count)) if count > 0 else "number"
        )
        self.ctx.write(
            f"public {sanitized_getter}(index: {index_type}): {return_type} {{\n"
        )
        self.ctx.indent()
        self.ctx.write("const el = this.#elements[index - 1];\n")
        self.ctx.write("if (el === undefined) {\n")
        self.ctx.indent()
        self.ctx.write(
            f"throw new RangeError(`Index ${{index}} is out of range [1, {count}]`);\n"
        )
        self.ctx.dedent()
        self.ctx.write("}\n")
        self.ctx.write("return el;\n")
        self.ctx.dedent()
        self.ctx.write("}\n")

    def _parse_instances(self, reg_ex: str, instance) -> VssInstance:
        result = []
        range_name = _DEFAULT_RANGE_NAME
        if isinstance(instance, str):
            if re.match(reg_ex, instance):
                parts = [
                    p.strip()
                    for p in re.split(r"\[+|,+|\]+", instance)
                    if p.strip()
                ]
                range_name = parts[0]
                lower_bound = int(parts[1])
                upper_bound = int(parts[2])
                for element in range(lower_bound, upper_bound + 1):
                    item = f"{range_name}{element}"
                    sanitize_ts_identifier(item)
                    result.append(item)
                return VssInstance(range_name, result, True)
            raise ValueError(f"Instantiation type {instance} not supported")

        if isinstance(instance, list):
            for element in instance:
                item = f"{element}".strip()
                sanitize_ts_identifier(item)
                result.append(item)
            return VssInstance(range_name, result, False)

        raise ValueError(f"Instance {instance} of type {type(instance)} is unsupported")
