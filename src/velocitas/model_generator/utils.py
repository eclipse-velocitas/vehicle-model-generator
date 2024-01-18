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
from typing import Optional


def camel_to_snake_case(input: str) -> str:
    separation_pattern = (
        r"[A-Z]?[a-z]+|[A-Z]{2,}(?=[A-Z][a-z]|\d|\W|$)|\d+|[A-Z]{2,}|[A-Z]"
    )
    parts = re.findall(separation_pattern, input)
    return "_".join(map(str.lower, parts))


class CodeGeneratorContext:
    """CodeGeneratorContext."""

    def __init__(self):
        """init."""
        self.model_code = []
        self.tab = "    "
        self.line_break = "\n"
        self.level = 0
        self.position = 0

    def __enter__(self):
        """enter."""
        self.indent()
        return self

    def __exit__(self, type, value, traceback):
        """exit."""
        self.dedent()

    def reset(self):
        """Reset the generated model code."""
        self.model_code = []
        self.position = 0

    def set_position(self, position: int):
        """Set the position of the writing cursor in the generated model code."""
        self.position = position

    def get_content(self):
        """Return the content of the generated model code."""
        code = "".join(self.model_code)
        return code

    def write(
        self,
        text: str,
        index: Optional[int] = None,
        strip_lines: bool = False,
        replace_char: str = "|",
        ignore_initial_line=False,
    ):
        """Write to the generated model code at the specified index."""
        lines = text.split(self.line_break)

        i = 0
        for line in lines:
            if strip_lines:
                line = line.strip().replace(replace_char, "")

            if ignore_initial_line and i == 0:
                i += 1
                continue

            line_prefix = self.tab * self.level if line else ""
            line_suffix = self.line_break if i < (len(lines) - 1) else ""
            i += 1
            if index is not None:
                self.model_code.insert(index, line_prefix + line + line_suffix)
            else:
                # if appending at the current position, consider if the previous
                # line was terminated to apply the line prefix
                if self.position > 0:
                    prev_line = self.model_code[self.position - 1]
                    if len(prev_line) > 0 and not prev_line[-1] == self.line_break:
                        line_prefix = ""
                self.model_code.insert(self.position, line_prefix + line + line_suffix)
                self.position += 1

    def indent(self):
        """Increase the indentation level."""
        self.level += 1

    def dedent(self):
        """Decrease the indentation level."""
        if self.level == 0:
            raise SyntaxError("internal error in code generator")
        self.level -= 1
