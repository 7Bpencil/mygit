import argparse
from mygit.command import Command


class Init(Command):
    def __init__(self, subparsers: argparse._SubParsersAction, commands_dict: dict):
        command_description = \
            "Create an empty Git repository in current directory"
        super().__init__("init", command_description, subparsers, commands_dict)

    def work(self, namespace: argparse.Namespace):
        print("PRINT IS WORKING!")
