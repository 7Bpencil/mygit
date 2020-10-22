import argparse
from mygit.command import Command
from textwrap import dedent
from file_system.abstract_file_system import AbstractFileSystem
from mygit.constants import Constants
from mygit.state import State
from mygit.backend import check_status, print_indexed_paths, print_ignored_paths, print_status


class Status(Command):
    def __init__(self, subparsers: argparse._SubParsersAction, commands_dict: dict):
        command_description = dedent(
            '''
            Shows status of all three trees: workspace, index, ignored

            Usage examples:
               mygit status              show status of workspace
               mygit status --indexed    show indexed paths
               mygit status --ignored    show ignored paths
            ''')

        super().__init__("status", command_description, subparsers, commands_dict)

    def __add_arguments(self, command_parser: argparse.ArgumentParser):
        status_group = command_parser.add_mutually_exclusive_group()
        status_group.add_argument('--indexed', action='store_true', default=False,
                                  help="show indexed paths")
        status_group.add_argument('--ignored', action='store_true', default=False,
                                  help="show ignored paths")

    def work(self, namespace: argparse.Namespace, file_system: AbstractFileSystem, constants: Constants, state: State):
        check_status(file_system, state)
        if namespace.indexed:
            print_indexed_paths(state)
        elif namespace.ignored:
            print_ignored_paths(state)
        else:
            print_status(file_system, constants, state)
