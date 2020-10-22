import argparse
from textwrap import dedent
from mygit.state import State
from mygit.constants import Constants
from mygit.command import Command
from mygit.backend import create_new_branch_from_current_and_checkout, checkout_to_branch


class Checkout(Command):
    def __init__(self, subparsers: argparse._SubParsersAction, commands_dict: dict):
        command_description = dedent(
            '''
            Restores workspace state so it becomes identical to another branch's recorded state

            Usage examples:
              mygit checkout dev      restores dev branch workspace
                                      Note: you can't checkout with indexed but uncommitted changes
                                      Note: you can't checkout to current/nonexistent branch

              mygit checkout -n exp   creates new branch from HEAD and checkouts to it.
                                      Note: it will not change your workspace or index
            ''')

        super().__init__("checkout", command_description, subparsers, commands_dict)

    def _add_arguments(self, command_parser: argparse.ArgumentParser):
        command_parser.add_argument("branch", nargs=1)
        command_parser.add_argument('-n', '--new_branch', action='store_true',
                                    default=False)

    def work(self, namespace: argparse.Namespace, constants: Constants, state: State):
        if namespace.new_branch:
            create_new_branch_from_current_and_checkout(namespace.branch[0], constants)
        else:
            checkout_to_branch(namespace.branch[0], constants, state)
