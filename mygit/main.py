import argparse
import logging
from textwrap import dedent
from pathlib import Path

from mygit.state import State
from mygit.constants import Constants
from mygit.commands.status import Status
from mygit.commands.reset import Reset
from mygit.commands.print import Print
from mygit.commands.merge import Merge
from mygit.commands.log import Log
from mygit.commands.init import Init
from mygit.commands.index import Index
from mygit.commands.commit import Commit
from mygit.commands.checkout import Checkout
from mygit.commands.branch import Branch

from mygit.backend import is_init, get_compressed_file_content, get_last_commit_index_content
from colorama import init as colorama_init, deinit as colorama_deinit, Fore


def main():
    colorama_init()

    parser = create_parser()
    subparsers = parser.add_subparsers(dest="command", title="mygit tools")
    commands = create_commands(subparsers)
    namespace = parser.parse_args()

    logging.basicConfig(filename="mygit.log", level=logging.NOTSET, format='%(message)s')
    constants = Constants(Path.cwd())
    state = State()

    if namespace.command is None:
        logging.info(Fore.YELLOW + "write command or use 'mygit -h' for help")
    else:
        if is_init(constants):
            handle_command(commands, namespace, constants, state)
        elif namespace.command == "init":
            commands[namespace.command].work(namespace, constants, state)
            logging.info(Fore.GREEN + "new repository is created")
        else:
            logging.info(Fore.YELLOW + "directory doesn't contain a repository. Use 'mygit init' to create new one")

    colorama_deinit()


def create_parser():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=dedent(
            '''
            mygit is small git-clone cvs.
            These are common mygit commands used in various situations:

            start work:
              init         Create an empty mygit repository

            work on the current change:
              index        Add file contents to the index
              reset        Undo your changes

            examine the history and state:
              status       Show the working tree status
              log          Show commit history
              print        Show content of recorded objects

            grow, mark and tweak your common history:
              commit       Record changes to the repository
              branch       List, create, or delete branches
              merge        Join two or more development histories together
              checkout     Switch branches
            ''')
    )

    return parser


def create_commands(subparsers: argparse._SubParsersAction):
    commands = {}

    Init(subparsers, commands)
    Status(subparsers, commands)
    Log(subparsers, commands)
    Index(subparsers, commands)
    Branch(subparsers, commands)
    Checkout(subparsers, commands)
    Print(subparsers, commands)
    Merge(subparsers, commands)
    Reset(subparsers, commands)
    Commit(subparsers, commands)

    return commands


def handle_command(commands: dict, namespace: argparse.Namespace, constants: Constants, state: State):
    state.load_cache(
        constants,
        get_compressed_file_content(constants.mygit_index_path),
        get_last_commit_index_content(constants))

    if namespace.command == "init":
        logging.info(Fore.YELLOW + "directory already contains the repository")
    else:
        commands[namespace.command].work(namespace, constants, state)
