import argparse
import logging
from colorama import Fore
from textwrap import dedent
from mygit.state import State
from mygit.constants import Constants
from mygit.command import Command
from mygit.backend import reset_to_commit_state, delete_indexed_changes, \
    reset_all_indexed_files_to_commit_state, clean_index, clear_workspace, \
    expand_tree, get_current_branch_path, get_last_tree_checksum


class Reset(Command):
    def __init__(self, subparsers: argparse._SubParsersAction, commands_dict: dict):
        command_description = dedent(
            '''
            Reset workspace or index tree for specific files or whole workspace

            Usage examples:
              mygit reset -i file1 file2 ...          if specified files was indexed, will clear them from index
                                                      so it will look like they are not indexed again.
                                                      Workspace won't be changed

              mygit reset -i                          clear whole index
                                                      so it will look like there's no any indexed changes
                                                      Workspace won't be changed

              mygit reset --hard -i file1 file2 ...   does the same that not --hard version,
                                                      but then replaces specified files in workspace
                                                      with their last recorded versions
                                                      Note: resetting new file will delete it

              mygit reset --hard -i                   replace all indexed files with their recorded versions and clear whole index

              mygit reset                             return whole workspace to last commited condition, all changes will be lost
            ''')

        super().__init__("reset", command_description, subparsers, commands_dict)

    def _add_arguments(self, command_parser: argparse.ArgumentParser):
        command_parser.add_argument("-i", "--index", nargs="*")
        command_parser.add_argument('--hard', action='store_true', default=False)

    def work(self, namespace: argparse.Namespace, constants: Constants, state: State):
        if namespace.index is not None:
            if len(namespace.index) > 0:
                if namespace.hard:
                    reset_to_commit_state(namespace.index, constants, state)
                    logging.info(Fore.GREEN + "specified indexed files were restored to their last recorded state")
                delete_indexed_changes(namespace.index, constants, state)
                logging.info(Fore.GREEN + "specified indexed changes were deleted from index")
            else:
                if namespace.hard:
                    reset_all_indexed_files_to_commit_state(constants, state)
                    logging.info(Fore.GREEN + "all indexed files were restored to their last recorded state")
                clean_index(constants)
                logging.info(Fore.GREEN + "index was cleaned")
        else:
            clear_workspace(constants, state)
            expand_tree(get_last_tree_checksum(get_current_branch_path(constants), constants), constants)
            logging.info(Fore.GREEN + "workspace was reset to last commit state")
