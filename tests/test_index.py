import mygit.backend as backend
import mygit.main as mygit
import pytest
import tempfile

from test_utils import *
from hashlib import sha1
from mygit.constants import Constants
from mygit.state import State
from pathlib import Path
from shlex import split as shlex_split
from zlib import decompress, compress


class TestInit:
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

    def test_index_new_file(self):
        mygit.main(self.cwd_path, shlex_split("init"))  # init new repository

        test_file_name = "readme.md"
        test_file_path = self.cwd_path / test_file_name
        with Path.open(test_file_path, "w") as test_file:  # create test file
            test_file.write("hello world")

        with Path.open(test_file_path, "rb") as test_file:
            content = compress(test_file.read(), -1)
            test_file_checksum = sha1(content).hexdigest()

        state = get_current_state(self.constants)
        assert state.status_not_indexed_paths == ['modified: readme.md']

        mygit.main(self.cwd_path, shlex_split("index readme.md"))  # index test file

        state = get_current_state(self.constants)
        assert state.status_not_indexed_paths == []  # yep everything is indexed
        assert test_file_path in state.current_indexed_paths
        assert state.current_indexed_paths.get(test_file_path) == test_file_checksum

    def test_index_file_update(self):
        mygit.main(self.cwd_path, shlex_split("init"))  # init new repository

        test_file_name = "readme.md"
        test_file_path = self.cwd_path / test_file_name
        with Path.open(test_file_path, "w") as test_file:  # create test file
            test_file.write("hello world")

        with Path.open(test_file_path, "rb") as test_file:
            content = compress(test_file.read(), -1)
            test_file_checksum = sha1(content).hexdigest()

        mygit.main(self.cwd_path, shlex_split("index readme.md"))  # index test file
        mygit.main(self.cwd_path, shlex_split("commit upd_readme"))  # fix file content

        state = get_current_state(self.constants)
        assert state.status_not_indexed_paths == []  # yep everything is indexed

        with Path.open(test_file_path, "a") as test_file:  # change test file
            test_file.write("goodbye!")

        state = get_current_state(self.constants)
        assert state.status_not_indexed_paths == ['modified: readme.md']  # yep we changed one file
        assert state.status_indexed_paths == []  # but haven't indexed it

        mygit.main(self.cwd_path, shlex_split("index readme.md"))  # index updated file

        state = get_current_state(self.constants)
        assert state.status_not_indexed_paths == []  # yep all changes are indexed
        assert state.status_indexed_paths == ['modified: readme.md']

    def test_index_delete_file(self):
        mygit.main(self.cwd_path, shlex_split("init"))  # init new repository

        test_file_name = "readme.md"
        test_file_path = self.cwd_path / test_file_name
        with Path.open(test_file_path, "w") as test_file:  # create test file
            test_file.write("hello world")

        mygit.main(self.cwd_path, shlex_split("index readme.md"))  # index test file
        mygit.main(self.cwd_path, shlex_split("commit upd_readme"))  # fix file content

        Path.unlink(test_file_path)  # delete test file
        state = get_current_state(self.constants)
        assert state.status_not_indexed_paths == ['deleted: readme.md']  # yep mygit knows that you deleted it
        assert state.current_indexed_paths == {}  # but not indexed that change

        mygit.main(self.cwd_path, shlex_split("index readme.md"))  # index removal

        state = get_current_state(self.constants)
        assert state.status_not_indexed_paths == []
        assert state.current_indexed_paths.get(test_file_path) == 'deleted'
        assert state.status_indexed_paths == ['deleted: readme.md']

        mygit.main(self.cwd_path, shlex_split("commit delete_readme"))  # commit changes
        state = get_current_state(self.constants)
        assert state.status_not_indexed_paths == []
        assert state.current_indexed_paths == {}
        assert state.status_indexed_paths == []  # we saved all changes

    def test_index_new_dir(self):
        pass

    def test_index_update_dir(self):
        pass

    def test_index_delete_dir(self):
        pass
