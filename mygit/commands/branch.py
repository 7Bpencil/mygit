import argparse
from textwrap import dedent
from mygit.state import State
from mygit.constants import Constants
from mygit.command import Command
from mygit.backend import remove_branch, create_new_branch_from_current, create_new_branch_from_commit, show_branches


class Branch(Command):
    def __init__(self, subparsers: argparse._SubParsersAction, commands_dict: dict):
        command_description = dedent(
            '''
            Bunch of tools for branching

            Usage examples:
              mygit branch -r dev              remove branch dev
                                               Note: you can't remove head/nonexistent branch

              mygit branch -l                  show all branches

              mygit branch -a expl y76ec54...  create new branch with name expl,
                                               that will point to commit y76ec54...
                                               Note: you can't create branch from nonexistent commit
                                                     you can't create branch with already existent name

              mygit branch -a expl HEAD        create new branch with name expl,
                                               that will point to head commit
            ''')

        super().__init__("branch", command_description, subparsers, commands_dict)

    def _add_arguments(self, command_parser: argparse.ArgumentParser):
        branch_group = command_parser.add_mutually_exclusive_group()
        branch_group.add_argument("-r", "--remove", nargs=1,
                                  metavar="branch",
                                  help="removes specified branch")

        branch_group.add_argument("-l", "--list", action='store_true',
                                  default=False,
                                  help="shows all branches")

        branch_group.add_argument("-a", "--add_from_commit", nargs=2,
                                  metavar="checksum",
                                  help="creates new branch from commit")

    def work(self, namespace: argparse.Namespace, constants: Constants, state: State):
        if namespace.remove is not None:
            remove_branch(namespace.remove[0], constants)
        elif namespace.add_from_commit is not None:
            if namespace.add_from_commit[1] == "HEAD":
                create_new_branch_from_current(namespace.add_from_commit[0], constants)
            else:
                create_new_branch_from_commit(namespace.add_from_commit[0], namespace.add_from_commit[1], constants)
        elif namespace.list:
            show_branches(constants)
        else:
            print(Fore.YELLOW + "write arguments")
