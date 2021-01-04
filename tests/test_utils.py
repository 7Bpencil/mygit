import mygit.backend as backend
from mygit.constants import Constants
from mygit.state import State
from pathlib import Path


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

    backend.check_status(c, state)

    return state
