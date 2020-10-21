import argparse
from mygit.command import Command
from textwrap import dedent


class Log(Command):
    def __init__(self, subparsers: argparse._SubParsersAction, commands_dict: dict):
        command_description = dedent(
            '''
            Shows commit history of current branch in classic format:
              $checksum
              $date
              $message

            Usage examples:
              mygit log [-o]
            ''')

        super().__init__("log", command_description, subparsers, commands_dict)

    def __add_arguments(self, command_parser: argparse.ArgumentParser):
        command_parser.add_argument('-o', '--oneline', action='store_true',
                                    default=False,
                                    help='change output style to "$checksum $message" format')

    def work(self, namespace: argparse.Namespace):
        print("LOG IS WORKING!")
