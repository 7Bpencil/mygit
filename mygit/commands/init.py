import argparse
from mygit.command import Command
from file_system.abstract_file_system import AbstractFileSystem
from mygit.constants import Constants
from mygit.state import State
from mygit.backend import index_object, create_ignored_paths, create_indexed_paths, make_commit


class Init(Command):
    def __init__(self, subparsers: argparse._SubParsersAction, commands_dict: dict):
        command_description = \
            "Create an empty Git repository in current directory"
        super().__init__("init", command_description, subparsers, commands_dict)

    def work(self, namespace: argparse.Namespace, file_system: AbstractFileSystem, constants: Constants, state: State):
        file_system.create_directory(constants.mygit_path)
        file_system.create_directory(constants.mygit_objects_path)
        file_system.create_directory(constants.mygit_refs_path)
        file_system.create_directory(constants.mygit_branches_path)
        file_system.create_directory(constants.mygit_index_dir_path)

        default_branch_name = "master"
        file_system.write_file_text(constants.mygit_head_path, default_branch_name)
        file_system.create_file(f"{constants.mygit_branches_path}/{default_branch_name}")
        file_system.create_file(constants.mygit_index_path)
        file_system.write_file_text(constants.mygit_ignore_path, ".mygit")

        index_object(constants.mygit_ignore_path, file_system, constants, state)
        create_ignored_paths(file_system, constants, state)
        create_indexed_paths(file_system, constants, state)
        make_commit("init", file_system, constants, state)
