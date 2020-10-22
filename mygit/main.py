import argparse
from colorama import init as colorama_init, deinit as colorama_deinit, Fore
from textwrap import dedent
from shlex import split
from pathlib import Path

from mygit.commands.init import Init
from mygit.commands.status import Status
from mygit.commands.log import Log
from mygit.commands.index import Index
from mygit.commands.branch import Branch
from mygit.commands.checkout import Checkout
from mygit.commands.print import Print
from mygit.commands.merge import Merge
from mygit.commands.reset import Reset
from mygit.commands.commit import Commit

from mygit.constants import Constants
from mygit.state import State

from mygit.backend import create_ignored_paths, create_indexed_paths, create_last_commit_index_state, is_init


def main():
    colorama_init()

    parser = create_parser()
    subparsers = parser.add_subparsers(dest="command", title="mygit tools")
    commands = create_commands(subparsers)
    # namespace = parser.parse_args()
    namespace = parser.parse_args(split("init"))

    constants = Constants(Path.cwd())
    state = State()

    if namespace.command is None:
        print(Fore.YELLOW + "write command or use 'mygit -h' for help")
    else:
        if is_init(constants):
            handle_command(commands, namespace, constants, state)
        elif namespace.command == "init":
            commands[namespace.command].work(namespace, constants, state)
            print(Fore.GREEN + "new repository is created")
        else:
            print(Fore.YELLOW + "directory doesn't contain a repository. Use 'mygit init' to create new one")

    colorama_deinit()


def create_parser():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=dedent(
            '''
            mygit is small git-clone cvs.
            These are common mygit commands used in various situations:

            start work:
              init         Create an empty Git repository

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
    create_ignored_paths(constants, state)
    create_indexed_paths(constants, state)
    create_last_commit_index_state(constants, state)

    if namespace.command == "init":
        print(Fore.YELLOW + "directory already contains the repository")
    else:
        commands[namespace.command].work(namespace, constants, state)


if __name__ == '__main__':
    main()
