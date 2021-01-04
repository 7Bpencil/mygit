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

    def test_init_in_clean_dir(self):
        assert not backend.is_init(self.constants)
        mygit.main(self.cwd_path, shlex_split("init"))  # init new repository
        assert backend.is_init(self.constants)  # yep

    def test_init_in_dir_with_files(self):
        test_file_name = "readme.md"
        test_file_path = self.cwd_path / test_file_name
        with Path.open(test_file_path, "w") as test_file:  # create test file
            test_file.write("hello world")

        assert not backend.is_init(self.constants)
        mygit.main(self.cwd_path, shlex_split("init"))  # init new repository
        assert backend.is_init(self.constants)  # yep

        state = get_current_state(self.constants)
        backend.check_status(self.constants, state)
        assert state.current_indexed_paths == {}
        assert state.status_not_indexed_paths == ['modified: readme.md']

    def test_init_in_corrupted_repository(self):
        assert not backend.is_init(self.constants)
        mygit.main(self.cwd_path, shlex_split("init"))  # init new repository
        assert backend.is_init(self.constants)

        Path.unlink(self.constants.mygit_head_path)
        remove_directory(self.constants.mygit_objects_path)  # now it's really corrupted
        assert not backend.is_init(self.constants)
        assert backend.has_collisions_with_service_files(self.constants)  # see?

        mygit.main(self.cwd_path, shlex_split("init"))  # let's try
        assert not backend.is_init(self.constants)  # doesn't want to work in such environment
