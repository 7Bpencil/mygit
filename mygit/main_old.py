import argparse
from colorama import init as colorama_init, deinit as colorama_deinit, Fore
from time import strftime
from textwrap import dedent
from hashlib import sha1
from pathlib import Path
from zlib import decompress, compress

workspace_path = Path.cwd()
mygit_ignore_path = workspace_path / ".mygit_ignore"
mygit_path = workspace_path / ".mygit"
mygit_index_dir_path = mygit_path / "index"
mygit_index_path = mygit_index_dir_path / "index"
mygit_head_path = mygit_path / "head"
mygit_objects_path = mygit_path / "objects"
mygit_refs_path = mygit_path / "refs"
mygit_branches_path = mygit_refs_path / "branches"

ignored_paths = set()
indexed_paths = dict()
workspace_commit_state = dict()

status_is_checked = False
status_indexed_paths = []
status_indexed_but_changed_paths = []
status_not_indexed_paths = []


def handle_command(namespace: argparse.Namespace):
    create_ignored_paths()
    create_indexed_paths()
    create_workspace_commit_state()

    if namespace.command == "init":
        print(Fore.YELLOW + "directory already contains the repository")
    elif namespace.command == "index":
        handle_index(namespace)
    elif namespace.command == "status":
        handle_status(namespace)
    elif namespace.command == "log":
        handle_log(namespace)
    elif namespace.command == "commit":
        make_commit(namespace.message[0])
    elif namespace.command == "print":
        handle_print(namespace)
    elif namespace.command == "checkout":
        handle_checkout(namespace)
    elif namespace.command == "merge":
        handle_merge(namespace)
    elif namespace.command == "branch":
        handle_branch(namespace)
    elif namespace.command == "reset":
        handle_reset(namespace)


def create_parser():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=dedent(
            '''
            MyGit is small git-clone cvs.
            These are common MyGit commands used in various situations:

            start work:
              init         Create an empty Git repository or reinitialize an existing one

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
    subparsers = parser.add_subparsers(dest="command", title="cvs tools")

    init_parser = subparsers.add_parser(
        "init",
        description="Create an empty Git repository or reinitialize an existing one"
    )

    status_parser = subparsers.add_parser(
        "status",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=dedent(
            '''
            Shows status of all three trees: workspace, index, ignored

            Usage examples:
               mygit status              show status of workspace
               mygit status --indexed    show indexed paths
               mygit status --ignored    show ignored paths
            ''')
    )
    status_group = status_parser.add_mutually_exclusive_group()
    status_group.add_argument('--indexed', action='store_true', default=False,
                              help="show indexed paths")
    status_group.add_argument('--ignored', action='store_true', default=False,
                              help="show ignored paths")

    log_parser = subparsers.add_parser(
        "log",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=dedent(
            '''
            Shows commit history of current branch in classic format:
              $checksum
              $date
              $message

            Usage examples:
              mygit log [-o]
            ''')
    )
    log_parser.add_argument('-o', '--oneline', action='store_true',
                            default=False,
                            help='change output style to "$checksum $message"')

    index_parser = subparsers.add_parser(
        "index",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=dedent(
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
    )
    index_parser.add_argument('-a', '--all', action='store_true', default=False,
                              help="index all changes in workspace")
    index_parser.add_argument("files", nargs="*",
                              help="files or directories to index")

    branch_parser = subparsers.add_parser(
        "branch",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=dedent(
            '''
            Bunch of tools for branching

            Usage examples:
              mygit branch -r dev              remove branch dev 
                                               Note: you can't remove head/nonexistent branch      

              mygit branch -l                  show all branches          

              mygit branch -a exp y76ec54...   create new branch with name exp, 
                                               that will point to commit y76ec54...
                                               Note: you can't create branch from nonexistent commit
                                                     you can't create branch with already existent name

              mygit branch -a hotfix HEAD      create new branch with name hotfix, 
                                               that will point to head commit

            ''')
    )
    branch_group = branch_parser.add_mutually_exclusive_group()
    branch_group.add_argument("-r", "--remove", nargs=1,
                              metavar="branch",
                              help="removes specified branch")

    branch_group.add_argument("-l", "--list", action='store_true',
                              default=False,
                              help="shows all branches")

    branch_group.add_argument("-a", "--add_from_commit", nargs=2,
                              metavar="checksum",
                              help="creates new branch from commit")

    checkout_parser = subparsers.add_parser(
        "checkout",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=dedent(
            '''
            Restores workspace state so it becomes identical to another branch's recorded state

            Usage examples:
              mygit checkout dev      restores dev branch workspace
                                      Note: you can't checkout with indexed but uncommited changes
                                      Note: you can't checkout to current/nonexistent branch

              mygit checkout -n exp   creates new branch from HEAD and checkouts to it.
                                      Note: it will not change your workspace or index

            ''')
    )
    checkout_parser.add_argument("branch", nargs=1)
    checkout_parser.add_argument('-n', '--new_branch', action='store_true',
                                 default=False)

    print_parser = subparsers.add_parser(
        "print",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=dedent(
            '''
            Show content of recorded objects

            Usage examples:
              mygit print checksum1 checksum2 ...    print content of compressed object files
                                                     Note: can take any amount of directories
            ''')
    )
    print_parser.add_argument("compressed_files", nargs="+")

    merge_parser = subparsers.add_parser(
        "merge",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=dedent(
            '''
            Fast-forward HEAD to another branch state (if it's possible)

            Usage examples:
              mygit merge dev       merge commits from dev into HEAD
                                    Note: fast-forward is possible only if HEAD commit's line 
                                          is subset of branch commit's line
            ''')
    )
    merge_parser.add_argument("merge_branch", nargs=1)

    reset_parser = subparsers.add_parser(
        "reset",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=dedent(
            '''
            Resets indexed changes of files
            Restores indexed files to their recorded by last commit state and clears index

            Usage examples:
              mygit reset -i file1 file2 ...          if specified files was indexed, will clear them from index 
                                                      so it will look like they are not indexed again.
                                                      Workspace won't be changed

              mygit reset -i                          clears whole index 
                                                      so it will look like there's not any indexed changes
                                                      Workspace won't be changed

              mygit reset --hard -i file1 file2 ...   does the same that not --hard version,
                                                      but then replaces specified files in workspace 
                                                      with their last recorded versions
                                                      Note: resetting new file will delete it

              mygit reset --hard -i                   replaces all indexed files with their recorded versions and clears whole index 

              mygit reset                             returns whole workspace to last commited condition, all changes will be lost
            ''')
    )
    reset_parser.add_argument("-i", "--index", nargs="*")
    reset_parser.add_argument('--hard', action='store_true', default=False)

    commit_parser = subparsers.add_parser(
        "commit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=dedent(
            '''
            Records all indexed changes in cvs

            Usage examples:
              mygit commit message      message will be shown in log
            ''')
    )
    commit_parser.add_argument("message", nargs=1)

    return parser


def init():
    Path.mkdir(mygit_path)
    Path.mkdir(mygit_objects_path)
    Path.mkdir(mygit_refs_path)
    Path.mkdir(mygit_branches_path)
    Path.mkdir(mygit_index_dir_path)
    default_branch_name = "master"
    with Path.open(mygit_head_path, "w") as head:
        head.write(default_branch_name)

    Path.open(mygit_branches_path / default_branch_name, 'w').close()
    Path.open(mygit_index_path, "w").close()

    with Path.open(mygit_ignore_path, "w") as ignore:
        lines = [".mygit", "mygit.py"]
        ignore.writelines("\n".join(lines))

    index_object(mygit_ignore_path)
    create_ignored_paths()
    create_indexed_paths()
    make_commit("init")


def is_init():
    return mygit_path.exists()


def create_ignored_paths():
    with Path.open(mygit_ignore_path, "r") as ignored:
        for path in ignored.readlines():
            absolute_path = workspace_path / path.strip()
            if path == "\n" or not absolute_path.exists():
                continue
            if absolute_path.is_file():
                add_file_in_ignored(absolute_path)
            else:
                add_directory_in_ignored(absolute_path)


def add_file_in_ignored(file_path: Path):
    ignored_paths.add(file_path)


def add_directory_in_ignored(dir_path: Path):
    add_file_in_ignored(dir_path)
    for child in dir_path.iterdir():
        if child.is_file():
            add_file_in_ignored(child)
        else:
            add_directory_in_ignored(child)


def create_indexed_paths():
    content = get_compressed_file_content(mygit_index_path)
    if content != "":
        for buffer in content.split("\n"):
            pair_path_blob = buffer.split()
            indexed_paths[workspace_path / pair_path_blob[0]] = pair_path_blob[1]


def write_down_index():
    result = list()
    for path in indexed_paths:
        result.append(str(path.relative_to(workspace_path)) + " " + indexed_paths[path])
    content = compress(bytes("\n".join(result), encoding="utf-8"), -1)
    with Path.open(mygit_index_path, "wb") as index:
        index.write(content)


def clean_index():
    for child in mygit_index_dir_path.iterdir():
        Path.unlink(child)
    Path.open(mygit_index_path, "w").close()


def create_workspace_commit_state():
    content = get_last_commit_workspace_state_content()
    for buffer in content.split("\n"):
        pair_path_blob = buffer.split()
        blob_path = workspace_path / pair_path_blob[0]
        blob_checksum = pair_path_blob[1]

        workspace_commit_state[blob_path] = blob_checksum


def write_down_workspace_state(workspace_state: dict):
    result = list()
    for path in workspace_state:
        result.append(str(path.relative_to(workspace_path)) + " " + workspace_state[path])
    content = compress(bytes("\n".join(result), encoding="utf-8"), -1)
    checksum = sha1(content).hexdigest()
    with Path.open(mygit_objects_path / checksum, "wb") as workspace_state_file:
        workspace_state_file.write(content)

    return checksum


def clear_workspace():
    for child in workspace_path.iterdir():
        if child not in ignored_paths:
            if child.is_file():
                Path.unlink(child)
            else:
                clear_directory(child)


def clear_directory(directory_path: Path):
    for child in directory_path.iterdir():
        if child not in ignored_paths:
            if child.is_file():
                Path.unlink(child)
            else:
                clear_directory(child)
    directory_path.rmdir()


def get_tree_content(saved_tree_checksum: str):
    content = dict()
    if saved_tree_checksum == "":
        return content

    saved_tree = get_compressed_file_content(mygit_objects_path / saved_tree_checksum).split("\n")
    for i in range(len(saved_tree)):
        buffer = saved_tree[i].split()
        object_type = buffer[0]
        path = workspace_path / buffer[1]
        checksum = buffer[2]

        if object_type not in content:
            content[object_type] = {path: checksum}
        elif path not in content[object_type]:
            content[object_type][path] = checksum
        else:
            print(Fore.RED + "path appears more than ones: " + str(path) + " whole tree: " + saved_tree)

    return content


def get_last_tree_checksum(branch_path: Path):
    last_commit_path = mygit_objects_path / get_last_commit_checksum(branch_path)
    return get_tree_checksum(last_commit_path)


def get_tree_checksum(commit_path: Path):
    return get_compressed_file_content(commit_path).split("\n")[0]


def get_current_branch_name():
    with Path.open(mygit_head_path, "r") as head:
        current_branch_name = head.read()
    return current_branch_name


def get_current_branch_path():
    return mygit_branches_path / get_current_branch_name()


def get_last_commit_checksum(branch_path: Path):
    with Path.open(branch_path, "r") as branch:
        last_commit_checksum = branch.read()
    return last_commit_checksum


def get_last_commit_workspace_state_content():
    commit_content = get_commit_content(get_last_commit_checksum(get_current_branch_path()))
    content_checksum = commit_content[1]
    return get_compressed_file_content(mygit_objects_path / content_checksum)


def get_compressed_file_content(file_path_absolute: Path):
    if file_path_absolute.stat().st_size == 0:
        return ""
    with Path.open(file_path_absolute, "rb") as file:
        content = decompress(file.read()).decode(encoding="utf-8")
    return content


# ===============================Commit==========================================
def make_commit(commit_message: str):
    if not has_uncommited_changes():
        print(Fore.YELLOW + "working tree is clean, you can't commit if there's no changes")
    elif len(status_indexed_paths) == 0:
        print(Fore.YELLOW + "you can't commit if your index is empty, use index <file1, file2, ...> to index changes")
    else:
        current_branch_path = get_current_branch_path()
        last_commit_checksum = get_last_commit_checksum(current_branch_path)
        create_commit(current_branch_path, commit_message, last_commit_checksum)


def create_commit(current_branch_path: Path, commit_message: str, parent_commit_checksum: str):
    new_workspace_state = dict()
    current_tree_checksum = create_tree(workspace_path, new_workspace_state)
    workspace_state_checksum = write_down_workspace_state(new_workspace_state)
    content_raw = bytes(
        current_tree_checksum + "\n" +
        workspace_state_checksum + "\n" +
        commit_message + "\n" +
        str(strftime("%c %z")) + "\n" +
        parent_commit_checksum, encoding="utf-8")
    content = compress(content_raw, -1)
    checksum = sha1(content).hexdigest()
    commit_path = mygit_objects_path / checksum
    with Path.open(commit_path, "wb") as commit:
        commit.write(content)
    with Path.open(current_branch_path, "w") as branch:
        branch.write(checksum)
    clean_index()


def create_tree(dir_path: Path, new_workspace_state: dict):
    tree_objects = []
    for child in dir_path.iterdir():
        if child in ignored_paths:
            continue
        if child.is_file():
            blob_checksum = create_blob(child)
            if blob_checksum is not None:
                tree_objects.append("blob " + str(child.relative_to(workspace_path)) + " " + blob_checksum)
                new_workspace_state[child] = blob_checksum
        else:
            tree_checksum = create_tree(child, new_workspace_state)
            if tree_checksum is not None:
                tree_objects.append("tree " + str(child.relative_to(workspace_path)) + " " + tree_checksum)

    if len(tree_objects) == 0:
        return None
    content_raw = bytes("\n".join(tree_objects), encoding="utf-8")
    content = compress(content_raw, -1)
    checksum = sha1(content).hexdigest()
    tree_path = mygit_objects_path / checksum
    if not tree_path.exists():
        with Path.open(tree_path, "wb") as tree:
            tree.write(content)

    return checksum


def create_blob(file_path: Path):
    if file_path in indexed_paths:
        indexed_checksum = indexed_paths[file_path]
        indexed_blob_path = mygit_index_dir_path / indexed_checksum
        if indexed_blob_path.exists():
            indexed_blob_path.rename(mygit_objects_path / indexed_checksum)
        return indexed_checksum
    elif file_path in workspace_commit_state:
        return workspace_commit_state[file_path]

    return None


# ===============================Checkout========================================
def handle_checkout(namespace: argparse.Namespace):
    if namespace.new_branch:
        create_new_branch_from_current_and_checkout(namespace.branch[0])
    else:
        checkout_to_branch(namespace.branch[0])


def checkout_to_branch(branch_name):
    branch_path = mygit_branches_path / branch_name
    if not branch_path.exists():
        print(Fore.RED + "branch " + branch_name + " doesn't exist")
    elif has_uncommited_changes():
        print(Fore.RED + "you can't checkout with uncommited changes, use commit or reset")  # TODO reset
    else:
        clear_workspace()
        expand_tree(get_last_tree_checksum(branch_path))

        with Path.open(mygit_head_path, "w") as head:
            head.write(branch_name)
        print(Fore.GREEN + "moved to branch " + branch_name)


def create_new_branch_from_current_and_checkout(new_branch_name: str):
    create_new_branch_from_current(new_branch_name)
    with Path.open(mygit_head_path, "w") as head:
        head.write(new_branch_name)
    print(Fore.GREEN + "moved to new branch " + new_branch_name)


def expand_tree(tree_checksum: str):
    tree_content = get_tree_content(tree_checksum)
    for type in tree_content:
        if type == "blob":
            for path in tree_content[type]:
                expand_blob(tree_content[type][path], path)
        else:
            for path in tree_content[type]:
                Path.mkdir(path)
                expand_tree(tree_content[type][path])


def expand_blob(blob_checksum: str, target_filename: Path):
    with Path.open(mygit_objects_path / blob_checksum, "rb") as source:
        content = decompress(source.read())

    with Path.open(target_filename, "wb") as file:
        file.write(content)


# ===============================Branch==========================================
def handle_branch(namespace: argparse.Namespace):
    if namespace.remove is not None:
        remove_branch(namespace.remove[0])
    elif namespace.add_from_commit is not None:
        if namespace.add_from_commit[1] == "HEAD":
            create_new_branch_from_current(namespace.add[0])
        else:
            create_new_branch_from_commit(namespace.add_commit[0], namespace.add_commit[1])
    elif namespace.list:
        show_branches()
    else:
        print(Fore.YELLOW + "write arguments")


def remove_branch(branch_name: str):
    branch_path = mygit_branches_path / branch_name
    if branch_name == get_current_branch_name():
        print(Fore.YELLOW + "you can't remove the branch, on which you are. Checkout to another branch first")
    elif not branch_path.exists():
        print(Fore.RED + "branch doesn't exist")
    else:
        with Path.open(branch_path, "r") as branch:
            commit_checksum = branch.read()
        Path.unlink(branch_path)
        print(Fore.GREEN + "Deleted branch " + branch_name + " (" + commit_checksum + ")")


def create_new_branch_from_current(new_branch_name: str):
    current_branch_path = get_current_branch_path()
    last_commit = get_last_commit_checksum(current_branch_path)
    create_new_branch_from_commit(new_branch_name, last_commit)


def create_new_branch_from_commit(branch_name: str, commit_checksum: str):
    branch_path = mygit_branches_path / branch_name
    commit_path = mygit_objects_path / commit_checksum
    if branch_path.exists():
        print(Fore.YELLOW + "branch " + branch_name + " already exists")
    elif not commit_path.exists():
        print(Fore.RED + "commit doesn't exist")
    else:
        with Path.open(branch_path, "w") as new_branch:
            new_branch.write(commit_checksum)
        print(Fore.GREEN + "new branch " + branch_name + " is created")


def show_branches():
    print("branches:")
    for branch_path in mygit_branches_path.iterdir():
        print(Fore.YELLOW + str(branch_path.relative_to(mygit_branches_path)))


# ================================Merge==========================================
def handle_merge(namespace: argparse.Namespace):
    merge(namespace.merge_branch[0])


def merge(branch_name: str):
    branch_path = mygit_branches_path / branch_name
    current_branch_name = get_current_branch_name()
    current_branch_path = mygit_branches_path / current_branch_name

    if not branch_path.exists():
        print(Fore.RED + "branch " + branch_name + " doesn't exist")
    else:
        from_commit_checksum = get_last_commit_checksum(current_branch_path)
        to_commit_checksum = get_last_commit_checksum(branch_path)
        if from_commit_checksum == to_commit_checksum:
            print(
                Fore.RED + "You can't merge " + current_branch_name + " with " + branch_name + ".\nBranches are pointing on the same commit")
        elif has_uncommited_changes():
            print(Fore.RED + "you can't merge with uncommited changes, use commit or reset")  # TODO reset
        elif can_be_fast_forwarded(from_commit_checksum, to_commit_checksum):
            clear_workspace()
            expand_tree(get_tree_checksum(mygit_objects_path / to_commit_checksum))

            with Path.open(current_branch_path, "w") as current_branch:
                current_branch.write(to_commit_checksum)

            print(Fore.GREEN + "merged " + branch_name + " into current branch")
            print(Fore.RESET + "you can safely delete branch " + branch_name + " with branch -r <branch_name>")
        else:
            print(Fore.RED + "Possible merging conflicts, fast-forward is impossible")


def can_be_fast_forwarded(from_commit_checksum: str, to_commit_checksum: str):
    commit_checksum = to_commit_checksum

    while commit_checksum != "":
        if commit_checksum == from_commit_checksum:
            return True
        commit_content = get_commit_content(commit_checksum)
        commit_checksum = get_commit_parent_commit(commit_content)
    return False


# =================================Reset=========================================
def handle_reset(namespace: argparse.Namespace):
    if namespace.index is not None:
        if len(namespace.index) > 0:
            if namespace.hard:
                reset_to_commit_state(namespace.index)
                print(Fore.GREEN + "specified indexed files were restored to their last recorded state")
            delete_indexed_changes(namespace.index)
            print(Fore.GREEN + "specified indexed changes were deleted from index")
        else:
            if namespace.hard:
                reset_all_indexed_files_to_commit_state()
                print(Fore.GREEN + "all indexed files were restored to their last recorded state")
            clean_index()
            print(Fore.GREEN + "index was cleaned")
    else:
        clear_workspace()
        expand_tree(get_last_tree_checksum(get_current_branch_path()))
        print(Fore.GREEN + "workspace was reset to last commit state")


def delete_indexed_changes(objects_to_reset: list):
    for object in objects_to_reset:
        object_path = workspace_path / object
        if not object_path.exists():
            delete_indexed_changes_file(object_path)  # TODO so we can't reset indexed deleted directory
        elif object_path.is_file():
            delete_indexed_changes_file(object_path)
        else:
            delete_indexed_changes_dir(object_path)

    if len(indexed_paths) == 0:
        clean_index()
    else:
        write_down_index()


def delete_indexed_changes_file(file_path_absolute: Path):
    if file_path_absolute in indexed_paths:
        blob_index_path = mygit_index_dir_path / indexed_paths.pop(file_path_absolute)
        if blob_index_path.exists():
            Path.unlink(blob_index_path)


def delete_indexed_changes_dir(dir_path_absolute: Path):
    for child in dir_path_absolute.iterdir():
        if child.is_file():
            delete_indexed_changes_file(child)
        else:
            delete_indexed_changes_dir(child)


def reset_to_commit_state(objects_to_reset: list):
    for object in objects_to_reset:
        object_path = workspace_path / object
        if not object_path.exists():
            reset_to_commit_state_file(object_path)  # TODO so we can't reset indexed deleted directory
        elif object_path.is_file():
            reset_to_commit_state_file(object_path)
        else:
            reset_to_commit_state_dir(object_path)


def reset_to_commit_state_file(file_path_absolute: Path):
    if file_path_absolute in indexed_paths:
        if file_path_absolute in workspace_commit_state:
            expand_blob(workspace_commit_state[file_path_absolute], file_path_absolute)
        else:
            Path.unlink(file_path_absolute)


def reset_to_commit_state_dir(dir_path_absolute: Path):
    for child in dir_path_absolute.iterdir():
        if child.is_file():
            reset_to_commit_state_file(child)
        else:
            reset_to_commit_state_dir(child)


def reset_all_indexed_files_to_commit_state():
    for path in indexed_paths:
        reset_to_commit_state_file(path)


# =================================Status========================================
def handle_status(namespace: argparse.Namespace):
    check_status()
    if namespace.indexed:
        print_indexed_paths()
    elif namespace.ignored:
        print_ignored_paths()
    else:
        print_status()


def has_uncommited_changes():
    check_status()
    return len(status_indexed_paths) + len(status_not_indexed_paths) > 0


def check_status():
    global status_is_checked
    if not status_is_checked:
        check_tree(workspace_path)
        check_deleted_files()
        status_is_checked = True


def print_status():
    print("On branch " + get_current_branch_name())

    if not has_uncommited_changes():
        print("nothing to commit, working tree is clean")

    if len(status_indexed_paths) > 0:
        print(Fore.RESET + "indexed changes:")
        for indexed in status_indexed_paths:
            print(Fore.GREEN + indexed)
        print()

    if len(status_not_indexed_paths) > 0:
        print(Fore.RESET + "not indexed changes:")
        for not_indexed in status_not_indexed_paths:
            print(Fore.RED + not_indexed)
        print()

    if len(status_indexed_but_changed_paths) > 0:
        print(Fore.RESET + "indexed files with new not indexed changes:")
        for indexed in status_indexed_but_changed_paths:
            print(Fore.YELLOW + indexed)
        print()


def check_blob(file_path: Path):
    with Path.open(file_path, "rb") as source:
        content = compress(source.read(), -1)
        checksum = sha1(content).hexdigest()
        relative_path = str(file_path.relative_to(workspace_path))
        message = "modified: " + relative_path

    if file_path in workspace_commit_state and workspace_commit_state[file_path] == checksum:
        return

    if file_path in indexed_paths:
        status_indexed_paths.append(message)
        if not indexed_paths[file_path] == checksum:
            status_indexed_but_changed_paths.append(message)
    else:
        status_not_indexed_paths.append(message)


def check_tree(dir_path: Path):
    for child in dir_path.iterdir():
        if child not in ignored_paths:
            if child.is_file():
                check_blob(child)
            else:
                check_tree(child)


def check_deleted_files():
    for path in workspace_commit_state:
        if not path.exists():
            message = "deleted: " + str(path.relative_to(workspace_path))
            if path not in indexed_paths:
                status_not_indexed_paths.append(message)
            else:
                status_indexed_paths.append(message)


def print_ignored_paths():
    print(Fore.YELLOW + "ignored paths:")
    for ignored in ignored_paths:
        print(str(ignored.relative_to(workspace_path)))


def print_indexed_paths():
    if len(indexed_paths) == 0:
        print(Fore.YELLOW + "index is empty, use index <file1, file2, ...> to index changes")
    else:
        print(Fore.RESET + "indexed paths:")
        for path in indexed_paths:
            print(Fore.GREEN + str(path.relative_to(workspace_path)) + " " + indexed_paths[path])


# ================================Index==========================================
def handle_index(namespace: argparse.Namespace):
    if namespace.all:
        index_all_changes()
    elif len(namespace.files) > 0:
        index_input_files(namespace.files)
    else:
        print(Fore.YELLOW + "use index -a or index <file1, file2, ...> to index changes")


def index_all_changes():
    for child in workspace_path.iterdir():
        index_object(child)
    index_deleted_files()
    write_down_index()


def index_input_files(files: list):
    if len(files) == 0:
        print(Fore.YELLOW + "you didn't mention any file")
    else:
        for file in files:
            index_object(workspace_path / file)
        write_down_index()


def index_object(file_path_absolute: Path):
    file_path_relative = str(file_path_absolute.relative_to(workspace_path))
    if not file_path_absolute.exists() and file_path_absolute not in workspace_commit_state:
        print(Fore.RED + "file or directory doesn't exist: " + file_path_relative)
    elif file_path_absolute in ignored_paths:
        print(Fore.YELLOW + "file has been ignored: " + file_path_relative)
    else:
        if not file_path_absolute.exists():  # TODO so we can't index deleted directory
            index_file(file_path_absolute)
        elif file_path_absolute.is_file():
            index_file(file_path_absolute)
        else:
            index_tree(file_path_absolute)


def index_tree(dir_path_absolute: Path):
    for child in dir_path_absolute.iterdir():
        if child not in ignored_paths:
            if child.is_file():
                index_file(child)
            else:
                index_tree(child)


def index_file(file_path_absolute: Path):
    if not file_path_absolute.exists():
        indexed_paths[file_path_absolute] = "deleted"
        return

    with Path.open(file_path_absolute, "rb") as source:
        content = compress(source.read(), -1)
        checksum = sha1(content).hexdigest()
        blob_path = mygit_objects_path / checksum
        blob_index_path = mygit_index_dir_path / checksum

    if (file_path_absolute in workspace_commit_state
            and workspace_commit_state[file_path_absolute] == checksum):
        return

    if file_path_absolute in indexed_paths:
        previous_indexed_checksum = indexed_paths[file_path_absolute]
        p_i_c_path = mygit_index_dir_path / previous_indexed_checksum
        if previous_indexed_checksum != checksum and p_i_c_path.exists():
            Path.unlink(p_i_c_path)

    indexed_paths[file_path_absolute] = checksum
    if not blob_index_path.exists() and not blob_path.exists():
        with Path.open(blob_index_path, "wb") as blob:
            blob.write(content)


def index_deleted_files():
    for path in workspace_commit_state:
        if not path.exists() and path not in indexed_paths:
            indexed_paths[path] = "deleted"


# ================================Log============================================
def handle_log(namespace: argparse.Namespace):
    print_function = print_commit_content_oneline if namespace.oneline else print_commit_content
    commit_checksum = get_last_commit_checksum(get_current_branch_path())
    while commit_checksum != "":
        commit_content = get_commit_content(commit_checksum)
        print_function(commit_checksum, commit_content)
        commit_checksum = get_commit_parent_commit(commit_content)


def get_commit_content(commit_checksum: str):
    return get_compressed_file_content(mygit_objects_path / commit_checksum).split("\n")


def get_commit_parent_commit(commit_content: list):
    return commit_content[4]


def print_commit_content(commit_checksum: str, content: list):
    print("commit: " + commit_checksum)
    print("date: " + content[3])
    print("message:")
    print("\n" + " " * 4 + content[2])
    print()


def print_commit_content_oneline(commit_checksum: str, content: list):
    print(commit_checksum + " " + content[2])


# ==================================Print========================================
def handle_print(namespace: argparse.Namespace):
    for file in namespace.compressed_files:
        print_compressed_object(file)
        print()
    if len(namespace.compressed_files) == 0:
        print(Fore.YELLOW + "print <checksum1, checksum2, ...> to print objects")


def print_compressed_object(checksum: str):
    object_path = mygit_objects_path / checksum
    if not object_path.exists():
        print(Fore.RED + "object doesn't exist")
        return
    print(get_compressed_file_content(object_path))


# ==================================Main=========================================
def main():
    colorama_init()
    parser = create_parser()
    namespace = parser.parse_args()

    if namespace.command is None:
        print(Fore.YELLOW + "write command or use 'mygit -h' for help")
    else:
        if is_init():
            handle_command(namespace)
        elif namespace.command == "init":
            init()
            print(Fore.GREEN + "new repository is created")
        else:
            print(Fore.YELLOW + "directory doesn't contain a repository. Use 'cvs init' to create new one")
    colorama_deinit()
