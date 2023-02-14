# Copyright (c) 2022-2023 Robert Bosch GmbH and Microsoft Corporation
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

"""VehicleModelCppGenerator."""

import os
import re
import shutil
from typing import Set

# Until vsspec issue will be fixed: https://github.com/COVESA/vss-tools/issues/208
from vspec.model.constants import VSSType  # type: ignore
from vspec.model.vsstree import VSSNode  # type: ignore

from sdv.model_generator.utils import CodeGeneratorContext


class VehicleModelCppGenerator:
    """Generate c++ code for vehicle model."""

    def __init__(self, root: VSSNode, target_folder: str, namespace: str):
        """Initialize the c++ generator.

        Args:
            root (_type_): the vspec tree root node.
        """
        self.root = root
        self.target_folder = target_folder
        self.ctx_header = CodeGeneratorContext()
        self.includes: Set[str] = set()
        self.external_includes: Set[str] = set()
        self.root_namespace = namespace

    def generate(self):
        """Generate c++ code for vehicle model."""
        self.root_path = os.path.join(self.target_folder, "include")
        path = os.path.join(self.root_path, self.target_folder)
        if os.path.exists(path):
            shutil.rmtree(path)
        os.makedirs(path)

        self.__gen_model(self.root, self.target_folder, True)
        self.__visit_nodes(self.root, self.target_folder)

    def __visit_nodes(self, node: VSSNode, parent_path: str):
        """Recursively render nodes."""
        for child in node.children:
            child_path = os.path.join(parent_path, child.name)
            path = os.path.join(self.root_path, child_path)
            if child.type == VSSType.BRANCH:
                if not os.path.exists(path):
                    os.makedirs(path)

                self.__gen_model(child, child_path)
                self.__visit_nodes(child, child_path)

    def __generate_opening_namespace_text(
        self, root_namespace: str, node: VSSNode
    ) -> str:
        return (
            "namespace "
            + "::".join([root_namespace] + self.__get_namespace_for_node(node))
            + " {\n"
        )

    def __generate_closing_namespace_text(
        self, root_namespace: str, node: VSSNode
    ) -> str:
        text = "::".join([root_namespace] + self.__get_namespace_for_node(node))
        return "} // namespace " + text + "\n"

    def __get_namespace_for_node(self, node: VSSNode) -> list[str]:
        result = [n.name.lower().replace("switch", "switch_") for n in node.path][0:-1]
        return result

    def __generate_guard_name(self, node: VSSNode) -> str:
        return "VMDL_" + "_".join([p.name.upper() for p in node.path]) + "_H"

    def __gen_header(self, node: VSSNode):
        guard_name = self.__generate_guard_name(node)
        self.ctx_header.write(
            f"""#ifndef {guard_name}
            #define {guard_name}\n\n""",
            strip_lines=True,
        )

    def __gen_footer(self, node: VSSNode):
        self.ctx_header.write(
            self.__generate_closing_namespace_text(self.root_namespace, node)
        )
        self.ctx_header.write(f"#endif // {self.__generate_guard_name(node)}\n")

    def __gen_imports(self, node: VSSNode):
        self.ctx_header.write('#include "sdk/DataPoint.h"\n')
        self.ctx_header.write('#include "sdk/Model.h"\n')
        self.ctx_header.write("\n")

        for imp in sorted(self.includes):
            if imp[0] == ".":
                imp = imp[2:]
            self.ctx_header.write(f'#include "{imp}.hpp"\n')

        if len(self.includes) > 0:
            self.ctx_header.write("\n")

        for inc in sorted(self.external_includes):
            self.ctx_header.write(f"#include <{inc}>\n")

        if len(self.external_includes) > 0:
            self.ctx_header.write("\n")

        self.includes.clear()
        self.external_includes.clear()

    def __gen_model_docstring(self, node: VSSNode):
        self.ctx_header.write(f"/** {node.name} model. */\n")

    def __document_member(self, node: VSSNode):
        self.ctx_header.write("/**\n")
        if node.type.value == "attribute":
            self.ctx_header.write(
                f"* {node.name}: {node.type.value} ({node.datatype.value})\n"
            )
        else:
            self.ctx_header.write(f"* {node.name}: {node.type.value}\n")

        self.ctx_header.write(f"* {node.description}\n")
        self.ctx_header.write("*\n")
        if len(node.comment) > 0:
            self.ctx_header.write(f"* {node.comment}\n")
            self.ctx_header.write("*\n")

        if not isinstance(node.min, str) or not isinstance(node.max, str):
            self.ctx_header.write(f"* Value range: [{node.min}, {node.max}]\n")
        if hasattr(node, "unit"):
            self.ctx_header.write(f"* Unit: {node.unit}\n")
        if len(node.allowed) > 0:
            allowed_values = ", ".join(node.allowed)
            self.ctx_header.write(f"* Allowed values: {allowed_values}\n")
        self.ctx_header.write("**/\n")

    def __gen_nested_class(
        self, child: VSSNode, instances: list[tuple[str, list]], index: int
    ) -> str:
        child_namespace = "::".join(self.__get_namespace_for_node(child))
        name, values = instances[index]
        nested_name = (
            instances[index + 1][0] if index + 1 < len(instances) else child.name
        )
        nested_values = (
            instances[index + 1][1] if index + 1 < len(instances) else [child.name]
        )
        nested_type = (
            instances[index + 1][0]
            if index + 1 < len(instances) - 1
            else f"{child_namespace}::{child.name}"
        )

        if nested_type == "NamedRange":
            nested_type = instances[index + 1][1][0] + "Type"

        ctor_params = ""
        ctor_initializer_list = []
        ctor_initializer_str = ""
        method_list = []
        member_list = []
        member_list_str = ""
        class_name = ""

        if name.endswith("Collection"):
            ctor_params = "ParentClass* parent"
            ctor_initializer_list.append(f'ParentClass("{child.name}", parent)')
            class_name = name
        elif name.startswith("NamedRange"):
            name = values[0]
            ctor_params = "std::string name, ParentClass* parent"
            ctor_initializer_list.append(f"ParentClass(name, parent)")
            class_name = f"{name}Type"

            min_value = values[1]
            max_value = values[2] + 1
            self.external_includes.add("stdexcept")

        if nested_name == "Choice":
            for value in nested_values:
                ctor_initializer_list.append(f'{value}("{value}", this)')
                member_list.append(f"{nested_type} {value}")
        elif nested_name == "NamedRange":
            range_name = nested_values[0]
            min_value = nested_values[1]
            max_value = nested_values[2]
            for value in range(min_value, max_value + 1):
                ctor_initializer_list.append(
                    f'{range_name}{value}("{range_name}{value}", this)'
                )
                member_list.append(f"{nested_type} {range_name}{value}")

            method_context = CodeGeneratorContext()
            method_context.write(f"{nested_type}& {range_name}(int index) {{\n")
            with method_context as method_scope:
                for v in range(min_value, max_value + 1):
                    method_scope.write(f"if (index == {v}) {{\n")
                    with method_scope as return_scope:
                        return_scope.write(f"return {range_name}{v};\n")
                    method_scope.write("}\n")
                method_scope.write(
                    f'throw std::runtime_error("Given value is outside of allowed range\
                        [{min_value};{max_value}]!");\n'
                )
                self.external_includes.add("stdexcept")
            method_context.write("}\n")
            method_list.append(method_context.get_content())

        ctor_initializer_str = ",\n".join(ctor_initializer_list)

        # generate class code
        class_code_context = CodeGeneratorContext()
        class_code_context.write(
            f"class {class_name} : \
                                 public ParentClass {{\n"
        )

        # one indentation is lost after the first line when using replace,
        # that`s why we add an additional one for nested classes
        if class_name.endswith("Type"):
            class_code_context.indent()

        class_code_context.write("public:\n")

        with class_code_context as public_scope:
            if name.endswith("Collection"):
                public_scope.write("%NESTED_CLASSES%\n")
            public_scope.write(f"{class_name}({ctor_params})")
            if len(ctor_initializer_str) > 0:
                with public_scope as ctor_initializer_list_scope:
                    ctor_initializer_list_scope.write(f":\n{ctor_initializer_str}\n")
                public_scope.write("{\n}\n\n")

            if len(method_list) > 0:
                public_scope.write("\n\n".join(method_list))
                public_scope.write("\n")

            member_list_str = ";\n".join(member_list)
            public_scope.write(f"{member_list_str}" + ";\n")

        class_code_context.write("};\n")
        return class_code_context.get_content()

    def __gen_collection_types(self, node: VSSNode, path: str) -> str:
        collection_types = []
        for child in node.children:
            if child.type == VSSType.BRANCH:
                self.includes.add(f"{path}/{child.name}/{child.name}")

                if child.instances:
                    instances = [
                        (f"{child.name}Collection", [])
                    ] + self.__gen_instances(child)
                    generated_classes = []

                    # create all nested classes for this sub-tree
                    for i in range(len(instances) - 1):
                        nested_class = self.__gen_nested_class(child, instances, i)
                        generated_classes.append(nested_class)

                    collection_types.append(
                        generated_classes[0].replace(
                            "%NESTED_CLASSES%", "\n\n".join(generated_classes[1:])
                        )
                    )

        return "\n\n".join(collection_types)

    def __gen_model(self, node: VSSNode, path: str, is_root=False):
        # must be done before generating the imports, since it is adding imports
        # to the list
        collection_types = self.__gen_collection_types(node, path)

        self.__gen_header(node)
        self.__gen_imports(node)
        self.ctx_header.write(
            self.__generate_opening_namespace_text(self.root_namespace, node)
        )
        # Provide an alias for the parent class to avoid name conflicts with members
        self.ctx_header.write("using ParentClass = Model;\n\n")
        self.__gen_model_docstring(node)
        self.ctx_header.write(f"class {node.name} : public ParentClass {{\n")
        self.ctx_header.write("public:\n")

        with self.ctx_header as header_public:
            header_public.write(collection_types)
            header_public.write("\n")

            if is_root:
                header_public.write(f"{node.name}() :\n")
                header_public.indent()
                header_public.write('ParentClass("Vehicle")')
            else:
                header_public.write(
                    f"{node.name}(const std::string& name, ParentClass* parent) :\n"
                )
                header_public.indent()
                header_public.write("ParentClass(name, parent)")

            header_public.write("%MEMBER%\n")
            header_public.dedent()
            header_public.write("{}\n\n")

            # create members
            member = ""
            for child in node.children:
                child_namespace = "::".join(self.__get_namespace_for_node(child))
                self.__document_member(child)

                if child.type.value in ("attribute", "sensor", "actuator"):
                    header_public.write(
                        f"DataPoint{self.__get_data_type(child.datatype.value)} \
                            {child.name};\n\n"
                    )
                    member += ",\n\t\t" + f'{child.name}("{child.name}", this)'

                if child.type == VSSType.BRANCH:
                    if child.instances:
                        header_public.write(f"{child.name}Collection {child.name};\n\n")
                        member += ",\n\t\t" + f"{child.name}(this)"
                    else:
                        header_public.write(
                            f"{child_namespace}::{child.name} {child.name};\n\n"
                        )
                        member += ",\n\t\t" + f'{child.name}("{child.name}", this)'

        self.ctx_header.write("};\n")

        self.__gen_footer(node)

        with open(
            os.path.join(self.root_path, path, f"{node.name}.hpp"),
            "w",
            encoding="utf-8",
        ) as file:
            file.write(self.ctx_header.get_content().replace("%MEMBER%", member))

        self.ctx_header.reset()

    def __gen_instances(self, node: VSSNode) -> list[tuple[str, list]]:
        instances = node.instances

        reg_ex = r"\w+\[\d+,(\d+)\]"

        result: list[tuple[str, list]] = []

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

    def __parse_instances(self, reg_ex, i) -> tuple[str, list]:
        # parse string instantiation elements (e.g. Row[1,5])
        if isinstance(i, str):
            if re.match(reg_ex, i):
                inst_range_arr = re.split(r"\[+|,+|\]", i)
                range_name = inst_range_arr[0]
                lower_bound = int(inst_range_arr[1])
                upper_bound = int(inst_range_arr[2])
                return ("NamedRange", [range_name, lower_bound, upper_bound])

            raise ValueError("", "", "instantiation type not supported")

        # Use list elements for instances (e.g. ["LEFT","RIGHT"])
        if isinstance(i, list):
            return ("Choice", i)

        raise ValueError("", "", f"is of type {type(i)} which is unsupported")

    def __get_data_type(self, data_type: str) -> str:
        # there are no 8bit or 16bit types in grpc...
        data_type = data_type.replace("8", "32").replace("16", "32")
        if data_type[-1] == "]":
            return data_type[0].upper() + data_type[1:-2] + "Array"
        return data_type[0].upper() + data_type[1:]
