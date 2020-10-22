import argparse
from file_system.abstract_file_system import AbstractFileSystem
from mygit.constants import Constants
from mygit.state import State


class Command:
    def __init__(
            self, command_name: str, command_description: str,
            subparsers: argparse._SubParsersAction, commands_dict: dict):
        self.__add_subparser(command_name, command_description, subparsers)
        commands_dict[command_name] = self

    def __add_subparser(self, command_name: str, command_description: str, subparsers: argparse._SubParsersAction):
        command_parser = subparsers.add_parser(
            command_name,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=command_description
        )
        self.__add_arguments(command_parser)

    def __add_arguments(self, command_parser: argparse.ArgumentParser):
        pass

    def work(self, namespace: argparse.Namespace, file_system: AbstractFileSystem, constants: Constants, state: State):
        pass
