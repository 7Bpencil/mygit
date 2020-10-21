import argparse
from mygit.command import Command
from textwrap import dedent


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

    def work(self, namespace: argparse.Namespace):
        print("COMMIT IS WORKING!")
