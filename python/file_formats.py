from abc import abstractmethod
from typing import List
from python.constants import VSPEC, JSON
from vspec.model.vsstree import VSSNode
import vspec
import json

formats = [VSPEC, JSON]


class FileFormat:
    def __init__(self, file_path: str):
        self.file_path = file_path

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
                expand_inst=False
            )
            vspec.merge_tree(tree, overlay_tree)
        return tree


class Json(FileFormat):
    def __init__(self, file_path: str):
        super().__init__(file_path)

    def load_tree(self):
        output_json = json.load(open(self.file_path))
        tree = None
        for name, d in output_json.items():
            tree = self.__dictToNode(name, d)
        if tree is not None:
            for child in tree.children:
                child.parent = tree
        return tree

    def __dictToNode(self, name: str, d: dict):
        children = []
        if "children" in d:
            for child_name, child_d in d["children"].items():
                children.append(self.__dictToNode(child_name, child_d))
                '''node = self.__dictToNode(child_name, child_d)
                for child in node["children"].values():
                    child.parent = node
                children.append(node)'''
        return VSSNode(name, None, None, children)


