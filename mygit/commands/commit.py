import argparse
from textwrap import dedent
from mygit.state import State
from mygit.constants import Constants
from mygit.command import Command
from mygit.backend import make_commit


class Commit(Command):
    def __init__(self, subparsers: argparse._SubParsersAction, commands_dict: dict):
        command_description = dedent(
            '''
            Records all indexed changes in cvs

            Usage examples:
              mygit commit message      specified message will be shown in log
            ''')

        super().__init__("commit", command_description, subparsers, commands_dict)

    def __add_arguments(self, command_parser: argparse.ArgumentParser):
        command_parser.add_argument("message", nargs=1)

    def work(self, namespace: argparse.Namespace, constants: Constants, state: State):
        make_commit(namespace.message[0], constants, state)
