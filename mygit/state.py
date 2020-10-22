from mygit.constants import Constants
from mygit.backend import get_compressed_file_content, get_last_commit_index_content
from pathlib import Path


class State:
    def __init__(self):
        self.ignored_paths = set()
        self.current_indexed_paths = {}
        self.last_commit_indexed_path = {}

        self.status_is_checked = False
        self.status_indexed_paths = []
        self.status_indexed_but_changed_paths = []
        self.status_not_indexed_paths = []

    def load_cache(self, c: Constants):
        self.__create_ignored_paths(c)
        self.__create_indexed_paths(c)
        self.__create_last_commit_index_state(c)

    def __create_ignored_paths(self, c: Constants):
        with Path.open(c.mygit_ignore_path, "r") as ignored:
            for path in ignored.readlines():
                absolute_path = c.workspace_path / path.strip()
                if path == "\n" or not absolute_path.exists():
                    continue
                if absolute_path.is_file():
                    self.__add_file_in_ignored(absolute_path)
                else:
                    self.__add_directory_in_ignored(absolute_path)

    def __add_file_in_ignored(self, file_path: Path):
        self.ignored_paths.add(file_path)

    def __add_directory_in_ignored(self, dir_path: Path):
        self.__add_file_in_ignored(dir_path)
        for child in dir_path.iterdir():
            if child.is_file():
                self.__add_file_in_ignored(child)
            else:
                self.__add_directory_in_ignored(child)

    def __create_indexed_paths(self, c: Constants):
        content = get_compressed_file_content(c.mygit_index_path)
        self.__create_index(content, c)

    def __create_last_commit_index_state(self, c: Constants):
        content = get_last_commit_index_content(c)
        self.__create_index(content, c)

    def __create_index(self, content: str, c: Constants):
        if content != "":
            for buffer in content.split("\n"):
                pair_path_blob = buffer.split()
                blob_path = c.workspace_path / pair_path_blob[0]
                blob_checksum = pair_path_blob[1]
                self.current_indexed_paths[blob_path] = blob_checksum
