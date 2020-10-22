import argparse
from textwrap import dedent
from mygit.state import State
from mygit.constants import Constants
from mygit.command import Command
from mygit.backend import print_commit_content, print_commit_content_oneline, \
    get_last_commit_checksum, get_current_branch_path, \
    get_commit_content, get_commit_parent_commit


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

    def work(self, namespace: argparse.Namespace, constants: Constants, state: State):
        print_function = print_commit_content_oneline if namespace.oneline else print_commit_content
        commit_checksum = get_last_commit_checksum(get_current_branch_path(constants))
        while commit_checksum != "":
            commit_content = get_commit_content(commit_checksum, constants)
            print_function(commit_checksum, commit_content)
            commit_checksum = get_commit_parent_commit(commit_content)
