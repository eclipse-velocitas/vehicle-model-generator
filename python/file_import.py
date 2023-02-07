import re
from typing import List
from python.file_formats import formats, Json, Vspec
from python.constants import VSPEC, JSON

# if no other file supported format is found
class UnsupportedFileFormat(Exception):
    def __init__(self, *args, **kwargs):
        self.file_name = args[0]
        self.line_nr = args[1]
        self.message = args[2]
        Exception.__init__(self, *args, **kwargs)

    def __str__(self):
        return "{}: {}: {}".format(self.file_name, self.line_nr, self.message)


class FileImport:

    def __init__(self, file_path: str, include_dirs: List, strict, overlays):
        self.file_path = file_path
        self.include_dirs = include_dirs
        self.strict = strict
        self.overlays = overlays
        # setting the format from the file_path
        self.file_format = self.__get_format(self.file_path)

    def __get_format(self, file_path: str):
        for format in formats:
            if re.match(r"^.+\." + f"{format}" + r"$", file_path):
                if format == VSPEC:
                    return Vspec(file_path=self.file_path,
                                 include_dirs=self.include_dirs,
                                 strict=self.strict,
                                 overlays=self.overlays)
                elif format == JSON:
                    return Json(file_path=file_path)
        raise UnsupportedFileFormat(self.file_path, 0, "Input file format is not supported")

    def load_tree(self):
        return self.file_format.load_tree()
