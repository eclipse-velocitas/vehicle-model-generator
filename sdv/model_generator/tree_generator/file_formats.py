from abc import abstractmethod
from typing import List
from sdv.model_generator.tree_generator.constants import VSPEC, JSON
import vspec
import json

# supported file formats
formats = [VSPEC, JSON]


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
                expand_inst=False
            )
            vspec.merge_tree(tree, overlay_tree)
        return tree


class Json(FileFormat):
    def __init__(self, file_path: str):
        super().__init__(file_path)

    # VSS nodes have a field "$file_name", 
    # so it needs to be added for the vss-tools to work
    def extend_fields(self, d: dict):
        if "children" in d:
            for child_d in d["children"].values():
                self.extend_fields(child_d)
        d["$file_name$"] = ""
        return

    def load_tree(self):
        print("Loading json...")
        output_json = json.load(open(self.file_path))
        self.extend_fields(next(iter(output_json.values())))
        print("Generating tree from json...")
        tree = vspec.render_tree(output_json)
        return tree

