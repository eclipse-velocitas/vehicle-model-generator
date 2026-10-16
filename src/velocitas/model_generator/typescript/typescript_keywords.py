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

"""Reserved keywords of TypeScript / JavaScript language."""

import re

typescript_keywords = {
    "abstract",
    "any",
    "as",
    "async",
    "await",
    "boolean",
    "break",
    "case",
    "catch",
    "class",
    "const",
    "constructor",
    "continue",
    "debugger",
    "declare",
    "default",
    "delete",
    "do",
    "else",
    "enum",
    "export",
    "extends",
    "false",
    "finally",
    "for",
    "from",
    "function",
    "get",
    "if",
    "implements",
    "import",
    "in",
    "instanceof",
    "interface",
    "let",
    "module",
    "namespace",
    "never",
    "new",
    "null",
    "number",
    "of",
    "package",
    "private",
    "protected",
    "public",
    "readonly",
    "require",
    "return",
    "set",
    "static",
    "string",
    "super",
    "switch",
    "symbol",
    "this",
    "throw",
    "true",
    "try",
    "type",
    "typeof",
    "undefined",
    "unique",
    "unknown",
    "var",
    "void",
    "while",
    "with",
    "yield",
}

_IDENT = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")
_RESERVED_MEMBERS = {
    "name",
    "parent",
    "path",
    "broker",
    "constructor",
    "__proto__",
    "toJSON",
    "getPath",
}


def is_ts_keyword(identifier: str) -> bool:
    """Check if identifier is a TypeScript/JavaScript reserved keyword."""
    return identifier in typescript_keywords


def is_valid_ts_identifier(name: str) -> bool:
    """Check if identifier is a valid TypeScript/JavaScript identifier."""
    return bool(_IDENT.match(name))


def is_reserved_member(name: str) -> bool:
    """Check if identifier is a reserved member name on Model / JS Object."""
    return name in _RESERVED_MEMBERS


def sanitize_ts_identifier(name: str, fqn: str = "") -> str:
    """Sanitize identifier and validate against identifier syntax and reserved member names."""
    if not _IDENT.match(name):
        prefix = f"{fqn}: " if fqn else ""
        raise ValueError(f"{prefix}'{name}' is not a valid TypeScript identifier")
    if is_reserved_member(name) or is_ts_keyword(name):
        return f"{name}_"
    return name
