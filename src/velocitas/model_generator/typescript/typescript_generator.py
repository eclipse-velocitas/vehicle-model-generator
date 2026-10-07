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

"""VehicleModelTypescriptGenerator."""

import os
import shutil
from dataclasses import dataclass
from functools import cache
from string import Template
from typing import List, Optional, Set, Tuple, cast

from vss_tools.model import NodeType, VSSDataDatatype  # type: ignore
from vss_tools.tree import VSSNode  # type: ignore

from velocitas.model_generator.typescript.typescript_keywords import (
    sanitize_ts_identifier,
)
from velocitas.model_generator.typescript.vss_collection import VssCollection
from velocitas.model_generator.utils import CodeGeneratorContext


class UnsupportedDatatypeError(ValueError):
    """Raised when an unsupported datatype is encountered."""


@dataclass(frozen=True)
class _ResolvedMember:
    prop_name: str
    vss_name: str
    decl_type: str
    ctor_call: str
    doc_node: VSSNode
    branch_import: Optional[Tuple[str, str]] = None
    sdk_imports: Tuple[str, ...] = ()
    collection: Optional[VssCollection] = None


@dataclass(frozen=True)
class _TypeExport:
    raw_name: str
    package_list: Tuple[str, ...]
    rel_path: str
    is_collection: bool = False


_SCALARS = {
    "boolean": "Bool",
    "string": "String",
    "float": "Float",
    "double": "Double",
    "int8": "Int8",
    "int16": "Int16",
    "int32": "Int32",
    "int64": "Int64",
    "uint8": "Uint8",
    "uint16": "Uint16",
    "uint32": "Uint32",
    "uint64": "Uint64",
}


class VehicleModelTypescriptGenerator:
    """Generate TypeScript code for vehicle model."""

    @staticmethod
    def _get_data_attr(node: VSSNode, attr: str, default=None):
        if isinstance(node.data, dict):
            return node.data.get(attr, default)
        return getattr(node.data, attr, default)

    @classmethod
    def _get_node_type(cls, node: VSSNode) -> NodeType:
        node_type = cls._get_data_attr(node, "type")
        if isinstance(node_type, NodeType):
            return node_type
        return NodeType(node_type)

    @classmethod
    def _get_instances(cls, node: VSSNode):
        return cls._get_data_attr(node, "instances", None)

    def __init__(self, root_node: VSSNode, target_folder: str, root_package: str):
        self.root_node = root_node
        self.target_folder = target_folder
        self.root_package = root_package
        self.ctx = CodeGeneratorContext()
        self.branch_imports: Set[Tuple[str, str]] = set()
        self.sdk_imports: Set[str] = set()
        self.collections: List[VssCollection] = []
        self.type_exports: Set[_TypeExport] = set()

        if "." in root_package:
            self.root_package_list = root_package.split(".")
        elif "/" in root_package:
            self.root_package_list = [p for p in root_package.split("/") if p]
        else:
            self.root_package_list = [root_package]

    def generate(self):
        """Generate TypeScript code for vehicle model."""
        self.src_folder = os.path.join(self.target_folder, "src")
        os.makedirs(self.src_folder, exist_ok=True)

        self._gen_manifests()

        self._gen_model(self.root_node, self.root_package_list, is_root=True)
        self._visit_nodes(self.root_node, self.root_package_list)

        self._gen_factory()
        self._gen_types()
        self._gen_index()

    @classmethod
    def _get_templates_folder(cls) -> str:
        return os.path.join(os.path.dirname(__file__), "templates")

    @classmethod
    @cache
    def _get_license_header(cls) -> str:
        license_path = os.path.join(cls._get_templates_folder(), "LICENSE_HEADER.txt")
        with open(license_path, "r", encoding="utf-8") as f:
            return f.read().strip()

    def _gen_manifests(self):
        templates_folder = self._get_templates_folder()
        shutil.copy2(
            os.path.join(templates_folder, "tsconfig.json"),
            os.path.join(self.target_folder, "tsconfig.json"),
        )

        pkg_template_path = os.path.join(templates_folder, "package.json")
        with open(pkg_template_path, "r", encoding="utf-8") as f:
            template = Template(f.read())

        if self.root_package == "vehicle":
            pkg_name = "@velocitas/vehicle-model"
        elif self.root_package.startswith("@"):
            pkg_name = self.root_package
        else:
            pkg_name = f"@velocitas/{self.root_package.lower().replace('.', '-').replace('_', '-')}"

        content = template.substitute(PACKAGE_NAME=pkg_name)
        with open(
            os.path.join(self.target_folder, "package.json"),
            "w",
            encoding="utf-8",
            newline="\n",
        ) as f:
            f.write(content)

    def _gen_index(self):
        template_path = os.path.join(self._get_templates_folder(), "index.ts.template")
        with open(template_path, "r", encoding="utf-8") as f:
            template = Template(f.read())

        package_rel_path = "/".join(self.root_package_list)
        root_name = self.root_node.name

        index_content = template.substitute(
            LICENSE_HEADER=self._get_license_header(),
            PACKAGE_REL_PATH=package_rel_path,
            ROOT_NAME=root_name,
        )

        with open(
            os.path.join(self.src_folder, "index.ts"), "w", encoding="utf-8", newline="\n"
        ) as f:
            f.write(index_content)

    def _visit_nodes(self, node: VSSNode, parent_package_list: List[str]):
        """Recursively render nodes."""
        for child in node.children:
            child_package_list = parent_package_list + [child.name]

            if self._get_node_type(child) == NodeType.BRANCH:
                self._gen_model(child, child_package_list)
                self._visit_nodes(child, child_package_list)

    def _write_docstring_member(self, node: VSSNode):
        lines = []

        deprecation = self._get_data_attr(node, "deprecation", None)
        if deprecation:
            dep_str = str(deprecation).strip()
            if dep_str and dep_str != "True":
                lines.append(f"@deprecated {dep_str}".replace("*/", "* /"))
            else:
                lines.append("@deprecated")

        description = self._get_data_attr(node, "description", None)
        if description:
            lines.append(str(description).replace("*/", "* /"))

        comment = self._get_data_attr(node, "comment", None)
        if comment:
            lines.append(f"@remarks\n{str(comment).replace('*/', '* /')}")

        min_value = self._get_data_attr(node, "min", None)
        max_value = self._get_data_attr(node, "max", None)
        unit = self._get_data_attr(node, "unit", None)
        allowed = self._get_data_attr(node, "allowed", None)

        metadata_parts = []
        if unit:
            metadata_parts.append(f"Unit: {unit}")
        if isinstance(min_value, (int, float)) or isinstance(max_value, (int, float)):
            min_str = min_value if isinstance(min_value, (int, float)) else "-"
            max_str = max_value if isinstance(max_value, (int, float)) else "-"
            metadata_parts.append(f"Range: [{min_str}, {max_str}]")

        if metadata_parts:
            lines.append(" · ".join(metadata_parts))

        if allowed:
            lines.append(f"Allowed values: {', '.join(map(str, allowed))}")

        if not lines:
            return

        self.ctx.write("/**\n")
        for line in lines:
            for sub_line in line.split("\n"):
                self.ctx.write(f" * {sub_line}\n")
        self.ctx.write(" */\n")

    def _gen_model_docstring(self, node: VSSNode):
        lines = []
        description = self._get_data_attr(node, "description", None)
        if description:
            lines.append(str(description).replace("*/", "* /"))
        else:
            lines.append(f"{node.name} model.")

        fqn = self._get_fqn(node)
        if fqn:
            lines.append(f"@see {fqn}")

        self.ctx.write("/**\n")
        for line in lines:
            for sub_line in line.split("\n"):
                self.ctx.write(f" * {sub_line}\n")
        self.ctx.write(" */\n")

    @staticmethod
    def _get_fqn(node: VSSNode) -> str:
        return getattr(node.data, "fqn", node.name) or node.name

    def _check_case_collisions(self, node: VSSNode):
        seen_names: dict[str, VSSNode] = {}
        for child in node.children:
            lower = child.name.lower()
            if lower in seen_names:
                prev = seen_names[lower]
                raise ValueError(
                    f"Case collision between sibling nodes '{self._get_fqn(prev)}' and '{self._get_fqn(child)}'"
                )
            seen_names[lower] = child

    def _get_vss_type_name(self, datatype: str, node: VSSNode | None = None) -> str:
        base, is_array = (
            (datatype[:-2], True) if datatype.endswith("[]") else (datatype, False)
        )
        if base not in _SCALARS:
            fqn = self._get_fqn(node) if node else "Unknown"
            raise UnsupportedDatatypeError(
                f"{fqn}: datatype '{datatype}' is not supported by the TypeScript generator "
                f"(supported: {', '.join(sorted(_SCALARS.keys()))} and their [] variants)"
            )
        return f"{_SCALARS[base]}{'Array' if is_array else ''}VssType"

    def _get_leaf_type_info(self, child: VSSNode) -> Tuple[str, str, Tuple[str, ...]]:
        """Returns (decl_type, ctor_call, sdk_imports)."""
        child_type = self._get_node_type(child)
        raw_datatype = self._get_data_attr(child, "datatype")
        datatype_str = str(raw_datatype) if raw_datatype is not None else "string"
        vss_type = self._get_vss_type_name(datatype_str, child)

        if child_type == NodeType.SENSOR:
            return (
                f"Sensor<{vss_type}>",
                f'new Sensor("{child.name}", this)',
                ("Sensor", vss_type),
            )
        if child_type == NodeType.ACTUATOR:
            return (
                f"Actuator<{vss_type}>",
                f'new Actuator("{child.name}", this, {vss_type})',
                ("Actuator", vss_type),
            )
        # Attribute
        return (
            f"Attribute<{vss_type}>",
            f'new Attribute("{child.name}", this)',
            ("Attribute", vss_type),
        )

    def _get_branch_alias(self, parent_node: VSSNode, child: VSSNode) -> str:
        """Return identifier to use for child branch in parent class scope, aliasing if ambiguous."""
        reserved_in_file = {
            parent_node.name,
            f"{parent_node.name}Factory",
            "ModelFactory",
            "Branch",
            "Node",
            "Sensor",
            "Actuator",
            "Attribute",
            "VehicleDataBrokerClient",
        }
        for scalar in _SCALARS.values():
            reserved_in_file.add(f"{scalar}VssType")
            reserved_in_file.add(f"{scalar}ArrayVssType")

        if child.name in reserved_in_file:
            return f"{parent_node.name}_{child.name}"
        return child.name

    def _resolve_member(self, parent_node: VSSNode, child: VSSNode) -> _ResolvedMember:
        child_type = self._get_node_type(child)
        prop_name = sanitize_ts_identifier(child.name)
        vss_name = child.name

        if child_type == NodeType.BRANCH:
            branch_alias = self._get_branch_alias(parent_node, child)
            if self._get_instances(child):
                collection = VssCollection(child, element_type=branch_alias)
                return _ResolvedMember(
                    prop_name=prop_name,
                    vss_name=vss_name,
                    decl_type=collection.name,
                    ctor_call=f'new {collection.name}(this)',
                    doc_node=child,
                    branch_import=(child.name, branch_alias),
                    collection=collection,
                )
            return _ResolvedMember(
                prop_name=prop_name,
                vss_name=vss_name,
                decl_type=branch_alias,
                ctor_call=f'new {branch_alias}("{child.name}", this)',
                doc_node=child,
                branch_import=(child.name, branch_alias),
            )

        decl_type, ctor_call, sdk_imports = self._get_leaf_type_info(child)
        return _ResolvedMember(
            prop_name=prop_name,
            vss_name=vss_name,
            decl_type=decl_type,
            ctor_call=ctor_call,
            doc_node=child,
            sdk_imports=sdk_imports,
        )

    def _gen_model(
        self, node: VSSNode, package_list: List[str], is_root: bool = False
    ):
        self._check_case_collisions(node)
        self.ctx.reset()
        self.branch_imports.clear()
        self.sdk_imports.clear()
        self.collections.clear()

        # Resolve all members in a single pass
        members: List[_ResolvedMember] = [
            self._resolve_member(node, child) for child in node.children
        ]

        for m in members:
            if m.branch_import:
                self.branch_imports.add(m.branch_import)
            if m.sdk_imports:
                self.sdk_imports.update(m.sdk_imports)
            if m.collection:
                self.collections.append(m.collection)

        # Class definition
        self._gen_model_docstring(node)
        self.ctx.write(f"export class {node.name} extends Branch {{\n")
        self.ctx.indent()

        # Member declarations
        for m in members:
            self._write_docstring_member(m.doc_node)
            self.ctx.write(f"public readonly {m.prop_name}: {m.decl_type};\n\n")

        # Constructor
        if is_root:
            self.ctx.write(
                "constructor(client?: VehicleDataBrokerClient) {\n"
            )
            self.ctx.indent()
            self.ctx.write(f'super("{node.name}", undefined, client);\n\n')
        else:
            self.ctx.write(
                "constructor(name: string, parent?: Node, client?: VehicleDataBrokerClient) {\n"
            )
            self.ctx.indent()
            self.ctx.write("super(name, parent, client);\n\n")

        # Constructor member assignments
        for m in members:
            self.ctx.write(f"this.{m.prop_name} = {m.ctor_call};\n")

        self.ctx.dedent()
        self.ctx.write("}\n")
        self.ctx.dedent()
        self.ctx.write("}\n\n")

        # Write collection classes defined in this node
        for collection in self.collections:
            self.ctx.write(collection.ctx.get_content())

        class_code = self.ctx.get_content()
        header_content = self._build_header(package_list, is_root=is_root)

        # Track type exports for barrel file
        rel_file_path = "./" + "/".join(package_list) + f"/{node.name}.js"
        pkg_tuple = tuple(package_list)
        if not is_root:
            self.type_exports.add(_TypeExport(node.name, pkg_tuple, rel_file_path, False))
        for collection in self.collections:
            self.type_exports.add(_TypeExport(collection.name, pkg_tuple, rel_file_path, True))
            if getattr(collection, "has_inner_types", False):
                self.type_exports.add(
                    _TypeExport(collection.inner_type_name, pkg_tuple, rel_file_path, True)
                )

        # Write to file: src/<package_list>/<node.name>.ts
        dest_dir = os.path.join(self.src_folder, *package_list)
        os.makedirs(dest_dir, exist_ok=True)
        file_path = os.path.join(dest_dir, f"{node.name}.ts")
        with open(file_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(header_content + class_code)

    def _gen_factory(self):
        """Generate factory class for the root model in a separate file."""
        template_path = os.path.join(self._get_templates_folder(), "factory.ts.template")
        with open(template_path, "r", encoding="utf-8") as f:
            template = Template(f.read())

        root_name = self.root_node.name
        content = template.substitute(
            LICENSE_HEADER=self._get_license_header(),
            ROOT_NAME=root_name,
        )

        dest_dir = os.path.join(self.src_folder, *self.root_package_list)
        os.makedirs(dest_dir, exist_ok=True)
        file_path = os.path.join(dest_dir, f"{root_name}Factory.ts")
        with open(file_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)

    def _gen_types(self):
        """Generate src/types.ts exporting all node and collection types."""
        lines = [self._get_license_header(), ""]

        name_counts: dict[str, int] = {}
        for item in self.type_exports:
            name_counts[item.raw_name] = name_counts.get(item.raw_name, 0) + 1

        export_entries: List[Tuple[str, str, str]] = []
        for item in self.type_exports:
            if name_counts[item.raw_name] == 1:
                export_entries.append((item.raw_name, item.raw_name, item.rel_path))
            else:
                path_segments = item.package_list[1:] if len(item.package_list) > 1 else item.package_list
                qualified = "".join(path_segments)
                if item.is_collection:
                    qualified = f"{qualified}{item.raw_name}"
                export_entries.append((qualified, item.raw_name, item.rel_path))

        for export_name, raw_name, rel_path in sorted(export_entries):
            if export_name == raw_name:
                lines.append(f'export type {{ {raw_name} }} from "{rel_path}";')
            else:
                lines.append(f'export type {{ {raw_name} as {export_name} }} from "{rel_path}";')

        lines.append("\n")
        with open(
            os.path.join(self.src_folder, "types.ts"),
            "w",
            encoding="utf-8",
            newline="\n",
        ) as f:
            f.write("\n".join(lines))

    def _build_header(self, package_list: List[str], is_root: bool = False) -> str:
        """Build header containing license and imports for a model file."""
        lines = [self._get_license_header(), ""]

        sdk_symbols = {"Branch"}
        if not is_root or self.collections:
            sdk_symbols.add("Node")
        sdk_symbols.update(self.sdk_imports)
        sorted_symbols = sorted(sdk_symbols)

        lines.append("import {")
        for sym in sorted_symbols:
            lines.append(f"    {sym},")
        lines.append("    type VehicleDataBrokerClient,")
        lines.append('} from "vehicle-app-ts-sdk";')

        for b_name, alias in sorted(self.branch_imports):
            if b_name == alias:
                lines.append(f'import {{ {b_name} }} from "./{b_name}/{b_name}.js";')
            else:
                lines.append(f'import {{ {b_name} as {alias} }} from "./{b_name}/{b_name}.js";')

        lines.append("\n")
        return "\n".join(lines)
