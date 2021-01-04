import mygit.backend as backend
import mygit.main as mygit
import pytest
import tempfile

from hashlib import sha1
from mygit.constants import Constants
from mygit.state import State
from pathlib import Path
from shlex import split as shlex_split
from zlib import decompress, compress


def clean_directory(directory_path: Path):
    for child in directory_path.iterdir():
        if child.is_file():
            Path.unlink(child)
        else:
            remove_directory(child)


def remove_directory(directory_path: Path):
    clean_directory(directory_path)
    directory_path.rmdir()


def get_current_state(c: Constants) -> State:
    state = State()
    state.load_cache(
        c,
        backend.get_compressed_file_content(c.mygit_index_path),
        backend.get_last_commit_index_content(c))

    return state


class TestVCS:
    def setup_class(self):
        self.cwd = tempfile.TemporaryDirectory()
        self.cwd_path = Path(self.cwd.name)
        self.constants = Constants(self.cwd_path)

    def teardown_class(self):
        self.cwd.cleanup()
        pass

    def teardown_method(self, method):
        clean_directory(self.cwd_path)
        pass

    def test_functional(self):
        """Init new repository, create test file and save it in vcs"""
        assert not backend.is_init(self.constants)
        mygit.main(self.cwd_path, shlex_split("init"))  # init new repository

        test_file_name = "readme.md"
        test_file_path = self.cwd_path / test_file_name
        with Path.open(test_file_path, "w") as test_file:  # create test file
            test_file.write("hello world")

        with Path.open(test_file_path, "rb") as test_file:
            content = compress(test_file.read(), -1)
            test_file_checksum = sha1(content).hexdigest()

        state = get_current_state(self.constants)
        backend.check_status(self.constants, state)
        assert state.status_not_indexed_paths == ['modified: readme.md']

        mygit.main(self.cwd_path, shlex_split("index readme.md"))  # index test file

        state = get_current_state(self.constants)
        assert state.status_not_indexed_paths == []
        assert test_file_path in state.current_indexed_paths
        assert state.current_indexed_paths.get(test_file_path) == test_file_checksum

        mygit.main(self.cwd_path, shlex_split("commit created_readme"))  # save test file in vcs

        state = get_current_state(self.constants)
        assert state.current_indexed_paths == {}
        assert (self.constants.mygit_objects_path / test_file_checksum).exists()


