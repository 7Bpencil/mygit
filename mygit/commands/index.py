import argparse
from mygit.command import Command
from textwrap import dedent


class Index(Command):
    def __init__(self, subparsers: argparse._SubParsersAction, commands_dict: dict):
        command_description = dedent(
            '''
            Adds specified files to index for next commit.
            Only indexed changes will be recorded by cvs

            Usage examples:
              mygit index file1 file2    index changes in file1 and file2
                                         Note: can take any amount of files

              mygit index dir1 dir2      index changes in every not ignored file in specified directories
                                         Note: can take any amount of directories

              mygit index -a             index changes in every not ignored file of workspace
            ''')

        super().__init__("index", command_description, subparsers, commands_dict)

    def __add_arguments(self, command_parser: argparse.ArgumentParser):
        command_parser.add_argument('-a', '--all', action='store_true', default=False,
                                    help="index all changes in workspace")
        command_parser.add_argument("files", nargs="*",
                                    help="files or directories to index")

    def work(self, namespace: argparse.Namespace):
        print("INDEX IS WORKING!")
