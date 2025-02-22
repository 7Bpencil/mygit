import argparse
from textwrap import dedent
from mygit.state import State
from mygit.constants import Constants
from mygit.command import Command
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

    def _add_arguments(self, command_parser: argparse.ArgumentParser):
        command_parser.add_argument("merge_branch", nargs=1)

    def work(self, namespace: argparse.Namespace, constants: Constants, state: State):
        merge(namespace.merge_branch[0], constants, state)
