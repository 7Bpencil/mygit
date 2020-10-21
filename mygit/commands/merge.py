import argparse
from mygit.command import Command
from textwrap import dedent


class Merge(Command):
    def __init__(self, subparsers: argparse._SubParsersAction, commands_dict: dict):
        command_description = dedent(
            '''
            Fast-forward HEAD to another branch state (if it's possible)

            Usage examples:
              mygit merge dev       merge commits from dev into HEAD
                                    Note: fast-forward is possible only if HEAD commit's line
                                          is subset of branch commit's line
            ''')

        super().__init__("merge", command_description, subparsers, commands_dict)

    def __add_arguments(self, command_parser: argparse.ArgumentParser):
        command_parser.add_argument("merge_branch", nargs=1)

    def work(self, namespace: argparse.Namespace):
        print("MERGE IS WORKING!")
