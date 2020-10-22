import argparse
from mygit.command import Command
from textwrap import dedent
from file_system.abstract_file_system import AbstractFileSystem
from mygit.constants import Constants
from mygit.state import State
from mygit.backend import merge


class Merge(Command):
    def __init__(self, subparsers: argparse._SubParsersAction, commands_dict: dict):
        command_description = dedent(
            '''
            Fast-forward HEAD to another branch state (if it's possible)

            Usage examples:
              mygit merge dev       merge commits from dev into HEAD
                                    Note: fast-forward is possible only if HEAD commit's line
                                          is subset of branch commit's line
            ''')

        super().__init__("merge", command_description, subparsers, commands_dict)

    def __add_arguments(self, command_parser: argparse.ArgumentParser):
        command_parser.add_argument("merge_branch", nargs=1)

    def work(self, namespace: argparse.Namespace, file_system: AbstractFileSystem, constants: Constants, state: State):
        merge(namespace.merge_branch[0], file_system, constants, state)
