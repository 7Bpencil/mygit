import argparse
from mygit.command import Command
from textwrap import dedent


class Reset(Command):
    def __init__(self, subparsers: argparse._SubParsersAction, commands_dict: dict):
        command_description = dedent(
            '''
            Resets indexed changes of files
            Restores indexed files to their recorded by last commit state and clears index

            Usage examples:
              mygit reset -i file1 file2 ...          if specified files was indexed, will clear them from index
                                                      so it will look like they are not indexed again.
                                                      Workspace won't be changed

              mygit reset -i                          clears whole index
                                                      so it will look like there's no any indexed changes
                                                      Workspace won't be changed

              mygit reset --hard -i file1 file2 ...   does the same that not --hard version,
                                                      but then replaces specified files in workspace
                                                      with their last recorded versions
                                                      Note: resetting new file will delete it

              mygit reset --hard -i                   replaces all indexed files with their recorded versions and clears whole index

              mygit reset                             returns whole workspace to last commited condition, all changes will be lost
            ''')

        super().__init__("reset", command_description, subparsers, commands_dict)

    def __add_arguments(self, command_parser: argparse.ArgumentParser):
        command_parser.add_argument("-i", "--index", nargs="*")
        command_parser.add_argument('--hard', action='store_true', default=False)

    def work(self, namespace: argparse.Namespace):
        print("RESET IS WORKING!")
