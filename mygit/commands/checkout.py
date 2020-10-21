import argparse
from mygit.command import Command
from textwrap import dedent


class Checkout(Command):
    def __init__(self, subparsers: argparse._SubParsersAction, commands_dict: dict):
        command_description = dedent(
            '''
            Restores workspace state so it becomes identical to another branch's recorded state

            Usage examples:
              mygit checkout dev      restores dev branch workspace
                                      Note: you can't checkout with indexed but uncommited changes
                                      Note: you can't checkout to current/nonexistent branch

              mygit checkout -n exp   creates new branch from HEAD and checkouts to it.
                                      Note: it will not change your workspace or index
            ''')

        super().__init__("checkout", command_description, subparsers, commands_dict)

    def __add_arguments(self, command_parser: argparse.ArgumentParser):
        command_parser.add_argument("branch", nargs=1)
        command_parser.add_argument('-n', '--new_branch', action='store_true',
                                    default=False)

    def work(self, namespace: argparse.Namespace):
        print("CHECKOUT IS WORKING!")
