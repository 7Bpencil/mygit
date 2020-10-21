import argparse
from mygit.command import Command
from textwrap import dedent


class Print(Command):
    def __init__(self, subparsers: argparse._SubParsersAction, commands_dict: dict):
        command_description = dedent(
            '''
            Show content of recorded objects

            Usage examples:
              mygit print checksum1 checksum2 ...    print content of compressed object files
                                                     Note: can take any amount of files
            ''')

        super().__init__("print", command_description, subparsers, commands_dict)

    def __add_arguments(self, command_parser: argparse.ArgumentParser):
        command_parser.add_argument("compressed_files", nargs="+")

    def work(self, namespace: argparse.Namespace):
        print("PRINT IS WORKING!")
