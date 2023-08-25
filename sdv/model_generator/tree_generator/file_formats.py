# Copyright (c) 2023 Robert Bosch GmbH
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

import json
import re
from abc import abstractmethod
from typing import List

# Until vsspec issue will be fixed: https://github.com/COVESA/vss-tools/issues/208
import vspec  # type: ignore

from sdv.model_generator.tree_generator.constants import (
    JSON,
    VSPEC,
    VSS_KEY_CHILDREN,
    VSS_KEY_EXPANDED,
    VSS_KEY_FILENAME,
    VSS_KEY_INSTANCES,
)

# supported file formats
formats = [VSPEC, JSON]


class ExpansionMismatch(Exception):
    pass


class FileFormat:
    def __init__(self, file_path: str):
        self.file_path = file_path

    # method to override when adding a new format
    @abstractmethod
    def load_tree(self):
        pass


class Vspec(FileFormat):
    def __init__(self, file_path: str, include_dirs: List, strict, overlays):
        super().__init__(file_path)
        self.include_dirs = include_dirs
        self.strict = strict
        self.overlays = overlays

    def load_tree(self):
        print("Loading vspec...")
        tree = vspec.load_tree(
            self.file_path,
            self.include_dirs,
            merge_private=False,
            break_on_unknown_attribute=self.strict,
            break_on_name_style_violation=self.strict,
            expand_inst=False,
        )

        for overlay in self.overlays:
            print(f"Applying VSS overlay from {overlay}...")
            overlay_tree = vspec.load_tree(
                overlay,
                self.include_dirs,
                merge_private=False,
                break_on_unknown_attribute=self.strict,
                break_on_name_style_violation=self.strict,
                expand_inst=False,
            )
            vspec.merge_tree(tree, overlay_tree)
        return tree


class Json(FileFormat):
    def __init__(self, file_path: str):
        super().__init__(file_path)

    # Do a simple comparison of children names for now
    def __match(self, d1: dict, d2: dict):
        return d1.keys() == d2.keys()

    def __is_expanded(self, d: dict):
        return VSS_KEY_EXPANDED in d and d[VSS_KEY_EXPANDED]

    def __to_instance_description(self, instances):
        assert instances

        common_prefix = None
        indices = set()
        pattern = re.compile("([^0-9]+)([0-9]+)")
        for instance in instances:
            match = pattern.fullmatch(instance)
            if not match:
                return instances
            (prefix, index) = match.groups()
            if common_prefix is None:
                common_prefix = prefix
            elif prefix != common_prefix:
                return instances
            indices.add(int(index))

        min_index = None
        max_index = None
        for index in indices:
            if min_index is None:
                min_index = index  # sets are sorted
                max_index = index
            # make sure every index between min and (final) max is there
            elif index == max_index + 1:
                max_index = index
            else:
                return instances

        return f"{common_prefix}[{min_index},{max_index}]"

    def __generate_instance_list(self, instances):
        assert len(instances) > 0

        if len(instances) == 1:
            return self.__to_instance_description(instances[0])

        instance_list = []
        for instance_set in instances:
            instance_list.append(self.__to_instance_description(instance_set))
        return instance_list

    def __get_children(self, node: dict):
        if VSS_KEY_CHILDREN in node:
            return node[VSS_KEY_CHILDREN]
        return {}

    def __get_common_archetype_of_children(self, node: dict):
        common_archetype = None
        instances: list[list] = []

        this_instances = []
        for child_name, child_attrs in self.__get_children(node).items():
            (archetype, sub_instances) = self.__collapse_instances(child_attrs)
            if archetype:
                if common_archetype is None:
                    common_archetype = archetype
                    archetype_giver = child_name
                elif not self.__match(archetype, common_archetype):
                    raise ExpansionMismatch(
                        f"Nodes '{archetype_giver}' and '{child_name}' "
                        "contain diverging expanded children"
                    )
                if sub_instances:
                    if not instances:
                        instances = sub_instances
                    elif sub_instances != instances:
                        raise ExpansionMismatch(
                            f"Nodes '{archetype_giver}' and '{child_name}' "
                            "have diverging nested instances:\n"
                            f"{instances} and {sub_instances}"
                        )
                elif instances:
                    raise ExpansionMismatch(
                        f"Nodes '{archetype_giver}' and '{child_name}' "
                        "have diverging nested instances:\n"
                        f"{instances} and {sub_instances}"
                    )
                this_instances.append(child_name)
        if this_instances:
            instances.insert(0, this_instances)

        return (common_archetype, instances)

    def __collapse_instances(self, node: dict):
        (common_archetype, instances) = self.__get_common_archetype_of_children(node)

        if self.__is_expanded(node):
            if not common_archetype:
                common_archetype = node[VSS_KEY_CHILDREN]
            return (common_archetype, instances)

        if common_archetype:
            # Remove expanded children
            for child_name in instances[0]:
                del node[VSS_KEY_CHILDREN][child_name]

            if self.__is_expanded(node):
                # if this layer is also an expanded one, in the layer below
                # no children must be left
                if node[VSS_KEY_CHILDREN]:
                    raise ExpansionMismatch(
                        f'Node "{child_name}" has children other than instances:\n'
                        + node[VSS_KEY_CHILDREN]
                    )
            else:
                # if this layer is not an expanded one, the children of the
                # common_archetype needs to become children of this layer ...
                node[VSS_KEY_CHILDREN] |= common_archetype

                # ... and we need to genrate the list of instances
                node[VSS_KEY_INSTANCES] = self.__generate_instance_list(instances)

                common_archetype = None
                instances = []

        return (common_archetype, instances)

    # VSS nodes have a field "$file_name",
    # so it needs to be added for the vss-tools to work
    def __extend_fields(self, node: dict):
        for child in self.__get_children(node).values():
            self.__extend_fields(child)
        node[VSS_KEY_FILENAME] = ""
        return

    def load_tree(self):
        print("Loading json...")
        output_json = json.load(open(self.file_path))
        print("Collapsing expanded instances...")
        self.__collapse_instances(next(iter(output_json.values())))
        print("Generating tree from json...")
        self.__extend_fields(next(iter(output_json.values())))
        tree = vspec.render_tree(output_json)
        return tree
