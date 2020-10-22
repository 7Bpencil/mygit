import argparse
from mygit.state import State
from mygit.constants import Constants
from mygit.command import Command
from mygit.backend import index_object, create_ignored_paths, create_indexed_paths, make_commit
from pathlib import Path


class Init(Command):
    def __init__(self, subparsers: argparse._SubParsersAction, commands_dict: dict):
        command_description = \
            "Create an empty Git repository in current directory"
        super().__init__("init", command_description, subparsers, commands_dict)

    def work(self, namespace: argparse.Namespace, constants: Constants, state: State):
        Path.mkdir(constants.mygit_path)
        Path.mkdir(constants.mygit_objects_path)
        Path.mkdir(constants.mygit_refs_path)
        Path.mkdir(constants.mygit_branches_path)
        Path.mkdir(constants.mygit_index_dir_path)
        default_branch_name = "master"
        with Path.open(constants.mygit_head_path, "w") as head:
            head.write(default_branch_name)

        Path.open(constants.mygit_branches_path / default_branch_name, 'w').close()
        Path.open(constants.mygit_index_path, "w").close()

        with Path.open(constants.mygit_ignore_path, "w") as ignore:
            ignore.write(".mygit")

        index_object(constants.mygit_ignore_path, constants, state)
        create_ignored_paths(constants, state)
        create_indexed_paths(constants, state)
        make_commit("init", constants, state)
