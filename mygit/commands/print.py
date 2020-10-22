import argparse
import logging
from colorama import Fore
from textwrap import dedent
from mygit.state import State
from mygit.constants import Constants
from mygit.command import Command
from mygit.backend import print_compressed_object


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

    def _add_arguments(self, command_parser: argparse.ArgumentParser):
        command_parser.add_argument("compressed_files", nargs="+")

    def work(self, namespace: argparse.Namespace, constants: Constants, state: State):
        for file in namespace.compressed_files:
            print_compressed_object(file, constants)
        if len(namespace.compressed_files) == 0:
            logging.warning(Fore.YELLOW + "print <checksum1, checksum2, ...> to print objects")
