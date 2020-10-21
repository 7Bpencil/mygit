import argparse
from colorama import init as colorama_init, deinit as colorama_deinit, Fore
from mygit.constants import Constants
from file_system.abstract_file_system import AbstractFileSystem
from time import strftime
from textwrap import dedent
from hashlib import sha1
from pathlib import Path
from zlib import decompress, compress


# workspace_path = Path.cwd()
# mygit_ignore_path = workspace_path / ".mygit_ignore"
# mygit_path = workspace_path / ".mygit"
# mygit_index_dir_path = mygit_path / "index"
# mygit_index_path = mygit_index_dir_path / "index"
# mygit_head_path = mygit_path / "head"
# mygit_objects_path = mygit_path / "objects"
# mygit_refs_path = mygit_path / "refs"
# mygit_branches_path = mygit_refs_path / "branches"

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


def init(fs: AbstractFileSystem, c: Constants):
    fs.create_directory(c.mygit_path)
    fs.create_directory(c.mygit_objects_path)
    fs.create_directory(c.mygit_refs_path)
    fs.create_directory(c.mygit_branches_path)
    fs.create_directory(c.mygit_index_dir_path)

    default_branch_name = "master"
    fs.write_file_text(c.mygit_head_path, default_branch_name)
    fs.create_file(f"{c.mygit_branches_path}/{default_branch_name}")
    fs.create_file(c.mygit_index_path)
    fs.write_file_text(c.mygit_ignore_path, ".mygit")

    index_object(c.mygit_ignore_path, fs, c)
    create_ignored_paths(fs, c)
    create_indexed_paths(fs, c)
    make_commit("init", fs, c)


def is_init(fs: AbstractFileSystem, c: Constants):
    return fs.is_exist(c.mygit_path)


def create_ignored_paths(fs: AbstractFileSystem, c: Constants):
    for path in fs.read_lines(c.mygit_ignore_path):
        path = path.strip()
        if path == "" or not fs.is_exist(path):
            continue
        if fs.is_file(path):
            add_file_in_ignored(path)
        else:
            add_directory_in_ignored(path, fs, c)


def add_file_in_ignored(file_path: str):
    ignored_paths.add(file_path)


def add_directory_in_ignored(dir_path: str, fs: AbstractFileSystem, c: Constants):
    add_file_in_ignored(dir_path)
    for child in fs.get_directory_files(dir_path):
        if fs.is_file(child):
            add_file_in_ignored(child)
        else:
            add_directory_in_ignored(child, fs, c)


def create_indexed_paths(fs: AbstractFileSystem, c: Constants):
    content = get_compressed_file_content(c.mygit_index_path, fs)
    if content != "":
        for buffer in content.split("\n"):
            pair_path_blob = buffer.split()
            indexed_paths[pair_path_blob[0]] = pair_path_blob[1]


def write_down_index(fs: AbstractFileSystem, c: Constants):
    result = list()
    for path in indexed_paths:
        result.append(f"{path} {indexed_paths[path]}")
    content = compress(bytes("\n".join(result), encoding="utf-8"), -1)
    fs.write_file_binary(c.mygit_index_path, content)


def clean_index(fs: AbstractFileSystem, c: Constants):
    for child in fs.get_directory_files(c.mygit_index_dir_path):
        fs.remove_file(child)
    fs.write_file_text(c.mygit_index_path, "")


def create_workspace_commit_state(fs: AbstractFileSystem, c: Constants):
    content = get_last_commit_workspace_state_content(fs, c)
    for buffer in content.split("\n"):
        pair_path_blob = buffer.split()
        blob_path = pair_path_blob[0]
        blob_checksum = pair_path_blob[1]

        workspace_commit_state[blob_path] = blob_checksum


def write_down_workspace_state(workspace_state: dict, fs: AbstractFileSystem, c: Constants):
    result = list()
    for path in workspace_state:
        result.append(f"{path} {workspace_state[path]}")
    content = compress(bytes("\n".join(result), encoding="utf-8"), -1)
    checksum = sha1(content).hexdigest()
    fs.write_file_binary(f"{c.mygit_objects_path}/{checksum}", content)

    return checksum


def clear_workspace(fs: AbstractFileSystem):
    for child in fs.get_directory_files("."):
        if child not in ignored_paths:
            if fs.is_file(child):
                fs.remove_file(child)
            else:
                clear_directory(child, fs)


def clear_directory(directory_path: str, fs: AbstractFileSystem):
    for child in fs.get_directory_files(directory_path):
        if child not in ignored_paths:
            if fs.is_file(child):
                fs.remove_file(child)
            else:
                clear_directory(child, fs)
    fs.remove_directory(directory_path)


def get_tree_content(saved_tree_checksum: str, fs: AbstractFileSystem, c: Constants):
    content = dict()
    if saved_tree_checksum == "":
        return content

    saved_tree = get_compressed_file_content(f"{c.mygit_objects_path}/{saved_tree_checksum}", fs).split("\n")
    for i in range(len(saved_tree)):
        buffer = saved_tree[i].split()
        object_type = buffer[0]
        path = buffer[1]
        checksum = buffer[2]

        if object_type not in content:
            content[object_type] = {path: checksum}
        elif path not in content[object_type]:
            content[object_type][path] = checksum
        else:
            print(Fore.RED + "path appears more than ones: " + str(path) + " whole tree: " + saved_tree)

    return content


def get_last_tree_checksum(branch_path: str, fs: AbstractFileSystem, c: Constants):
    last_commit_path = f"{c.mygit_objects_path}/{get_last_commit_checksum(branch_path, fs)}"
    return get_tree_checksum(last_commit_path, fs)


def get_tree_checksum(commit_path: str, fs: AbstractFileSystem):
    return get_compressed_file_content(commit_path, fs).split("\n")[0]


def get_current_branch_name(fs: AbstractFileSystem, c: Constants):
    return fs.get_file_content_text(c.mygit_head_path)


def get_current_branch_path(fs: AbstractFileSystem, c: Constants):
    return f"{c.mygit_branches_path}/{get_current_branch_name(fs, c)}"


def get_last_commit_checksum(branch_path: str, fs: AbstractFileSystem):
    return fs.get_file_content_text(branch_path)


def get_last_commit_workspace_state_content(fs: AbstractFileSystem, c: Constants):
    commit_content = get_commit_content(get_last_commit_checksum(get_current_branch_path(fs, c), fs), fs, c)
    content_checksum = commit_content[1]
    return get_compressed_file_content(f"{c.mygit_objects_path}/{content_checksum}", fs)


def get_compressed_file_content(file_path: str, fs: AbstractFileSystem):
    if fs.file_is_empty(file_path):
        return ""
    source = fs.get_file_content_binary(file_path)
    content = decompress(source).decode(encoding="utf-8")
    return content


#===============================Commit==========================================
def make_commit(commit_message: str, fs: AbstractFileSystem, c: Constants):
    if not has_uncommited_changes():
        print(Fore.YELLOW + "working tree is clean, you can't commit if there's no changes")
    elif len(status_indexed_paths) == 0:
        print(Fore.YELLOW + "you can't commit if your index is empty, use index <file1, file2, ...> to index changes")
    else:
        current_branch_path = get_current_branch_path(fs, c)
        last_commit_checksum = get_last_commit_checksum(current_branch_path, fs)
        create_commit(current_branch_path, commit_message, last_commit_checksum, fs, c)


def create_commit(current_branch_path: str, commit_message: str, parent_commit_checksum: str,
                  fs: AbstractFileSystem, c: Constants):
    new_workspace_state = dict()
    current_tree_checksum = create_tree(".", new_workspace_state, fs, c)
    workspace_state_checksum = write_down_workspace_state(new_workspace_state, fs, c)
    content_raw = bytes(
        current_tree_checksum + "\n" +
        workspace_state_checksum + "\n" +
        commit_message + "\n" +
        str(strftime("%c %z")) + "\n" +
        parent_commit_checksum, encoding="utf-8")
    content = compress(content_raw, -1)
    checksum = sha1(content).hexdigest()
    commit_path = f"{c.mygit_objects_path}/{checksum}"
    fs.write_file_binary(commit_path, content)
    fs.write_file_text(current_branch_path, checksum)
    clean_index(fs, c)


def create_tree(dir_path: str, new_workspace_state: dict, fs: AbstractFileSystem, c: Constants):
    tree_objects = []
    for child in fs.get_directory_files(dir_path):
        if child in ignored_paths:
            continue
        if fs.is_file(child):
            blob_checksum = create_blob(child, fs, c)
            if blob_checksum is not None:
                tree_objects.append(f"blob {child} {blob_checksum}")
                new_workspace_state[child] = blob_checksum
        else:
            tree_checksum = create_tree(child, new_workspace_state, fs, c)
            if tree_checksum is not None:
                tree_objects.append(f"tree {child} {tree_checksum}")

    if len(tree_objects) == 0:
        return None
    content_raw = bytes("\n".join(tree_objects), encoding="utf-8")
    content = compress(content_raw, -1)
    checksum = sha1(content).hexdigest()
    tree_path = f"{c.mygit_objects_path}/{checksum}"
    if not fs.is_exist(tree_path):
        fs.write_file_binary(tree_path, content)

    return checksum


def create_blob(file_path: str, fs: AbstractFileSystem, c: Constants):
    if file_path in indexed_paths:
        indexed_checksum = indexed_paths[file_path]
        indexed_blob_path = f"{c.mygit_index_dir_path}/{indexed_checksum}"
        if fs.is_exist(indexed_blob_path):
            fs.rename_file(indexed_blob_path, f"{c.mygit_objects_path}/{indexed_checksum}")
        return indexed_checksum
    elif file_path in workspace_commit_state:
        return workspace_commit_state[file_path]

    return None


#===============================Checkout========================================
def handle_checkout(namespace: argparse.Namespace, fs: AbstractFileSystem, c: Constants):
    if namespace.new_branch:
        create_new_branch_from_current_and_checkout(namespace.branch[0], fs, c)
    else:
        checkout_to_branch(namespace.branch[0], fs, c)


def checkout_to_branch(branch_name: str, fs: AbstractFileSystem, c: Constants):
    branch_path = f"{c.mygit_branches_path}/{branch_name}"
    if not fs.is_exist(branch_path):
        print(Fore.RED + "branch " + branch_name + " doesn't exist")
    elif has_uncommited_changes():
        print(Fore.RED + "you can't checkout with uncommited changes, use commit or reset")  # TODO reset
    else:
        clear_workspace(fs)
        expand_tree(get_last_tree_checksum(branch_path, fs, c), fs, c)

        fs.write_file_text(c.mygit_head_path, branch_name)
        print(Fore.GREEN + "moved to branch " + branch_name)


def create_new_branch_from_current_and_checkout(new_branch_name: str, fs: AbstractFileSystem, c: Constants):
    create_new_branch_from_current(new_branch_name, fs, c)
    fs.write_file_text(c.mygit_head_path, new_branch_name)
    print(Fore.GREEN + "moved to new branch " + new_branch_name)


def expand_tree(tree_checksum: str, fs: AbstractFileSystem, c: Constants):
    tree_content = get_tree_content(tree_checksum, fs, c)
    for obj_type in tree_content:
        if obj_type == "blob":
            for path in tree_content[obj_type]:
                expand_blob(tree_content[obj_type][path], path, fs, c)
        else:
            for path in tree_content[obj_type]:
                fs.create_directory(path)
                expand_tree(tree_content[obj_type][path], fs, c)


def expand_blob(blob_checksum: str, target_filename: str, fs: AbstractFileSystem, c: Constants):
    source = fs.get_file_content_binary(f"{c.mygit_objects_path}/{blob_checksum}")
    content = decompress(source)
    fs.write_file_binary(target_filename, content)


#===============================Branch==========================================
def handle_branch(namespace: argparse.Namespace, fs: AbstractFileSystem, c: Constants):
    if namespace.remove is not None:
        remove_branch(namespace.remove[0], fs, c)
    elif namespace.add_from_commit is not None:
        if namespace.add_from_commit[1] == "HEAD":
            create_new_branch_from_current(namespace.add[0], fs, c)
        else:
            create_new_branch_from_commit(namespace.add_commit[0], namespace.add_commit[1], fs, c)
    elif namespace.list:
        show_branches(fs, c)
    else:
        print(Fore.YELLOW + "write arguments")


def remove_branch(branch_name: str, fs: AbstractFileSystem, c: Constants):
    branch_path = f"{c.mygit_branches_path}/{branch_name}"
    if branch_name == get_current_branch_name(fs, c):
        print(Fore.YELLOW + "you can't remove the branch, on which you are. Checkout to another branch first")
    elif not fs.is_exist(branch_path):
        print(Fore.RED + "branch doesn't exist")
    else:
        commit_checksum = fs.get_file_content_text(branch_path)
        fs.remove_file(branch_path)
        print(Fore.GREEN + "Deleted branch " + branch_name + " (" + commit_checksum + ")")


def create_new_branch_from_current(new_branch_name: str, fs: AbstractFileSystem, c: Constants):
    current_branch_path = get_current_branch_path(fs, c)
    last_commit = get_last_commit_checksum(current_branch_path, fs)
    create_new_branch_from_commit(new_branch_name, last_commit, fs, c)


def create_new_branch_from_commit(branch_name: str, commit_checksum: str, fs: AbstractFileSystem, c: Constants):
    branch_path = f"{c.mygit_branches_path}/{branch_name}"
    commit_path = f"{c.mygit_objects_path}/{commit_checksum}"
    if fs.is_exist(branch_path):
        print(Fore.YELLOW + "branch " + branch_name + " already exists")
    elif not fs.is_exist(commit_path):
        print(Fore.RED + "commit doesn't exist")
    else:
        fs.write_file_text(branch_path, commit_checksum)
        print(Fore.GREEN + "new branch " + branch_name + " is created")


def show_branches(fs: AbstractFileSystem, c: Constants):
    print("branches:")
    for branch_path in fs.get_directory_files(c.mygit_branches_path):
        print(Fore.YELLOW + branch_path)


#================================Merge==========================================
def handle_merge(namespace: argparse.Namespace, fs: AbstractFileSystem, c: Constants):
    merge(namespace.merge_branch[0], fs, c)


def merge(branch_name: str, fs: AbstractFileSystem, c: Constants):
    branch_path = f"{c.mygit_branches_path}/{branch_name}"
    current_branch_name = get_current_branch_name(fs, c)
    current_branch_path = f"{c.mygit_branches_path}/{current_branch_name}"

    if not fs.is_exist(branch_path):
        print(Fore.RED + "branch " + branch_name + " doesn't exist")
    else:
        from_commit_checksum = get_last_commit_checksum(current_branch_path, fs)
        to_commit_checksum = get_last_commit_checksum(branch_path, fs)
        if from_commit_checksum == to_commit_checksum:
            print(Fore.RED + "You can't merge " + current_branch_name + " with " + branch_name + ".\nBranches are pointing on the same commit")
        elif has_uncommited_changes():
            print(Fore.RED + "you can't merge with uncommited changes, use commit or reset")  # TODO reset
        elif can_be_fast_forwarded(from_commit_checksum, to_commit_checksum, fs, c):
            clear_workspace(fs)
            expand_tree(get_tree_checksum(f"{c.mygit_objects_path}/{to_commit_checksum}", fs), fs, c)
            fs.write_file_text(current_branch_path, to_commit_checksum)

            print(Fore.GREEN + "merged " + branch_name + " into current branch")
            print(Fore.RESET + "you can safely delete branch " + branch_name + " with branch -r <branch_name>")
        else:
            print(Fore.RED + "Possible merging conflicts, fast-forward is impossible")


def can_be_fast_forwarded(from_commit_checksum: str, to_commit_checksum: str, fs: AbstractFileSystem, c: Constants):
    commit_checksum = to_commit_checksum

    while commit_checksum != "":
        if commit_checksum == from_commit_checksum:
            return True
        commit_content = get_commit_content(commit_checksum, fs, c)
        commit_checksum = get_commit_parent_commit(commit_content)
    return False


#=================================Reset=========================================
def handle_reset(namespace: argparse.Namespace, fs: AbstractFileSystem, c: Constants):
    if namespace.index is not None:
        if len(namespace.index) > 0:
            if namespace.hard:
                reset_to_commit_state(namespace.index, fs, c)
                print(Fore.GREEN + "specified indexed files were restored to their last recorded state")
            delete_indexed_changes(namespace.index, fs, c)
            print(Fore.GREEN + "specified indexed changes were deleted from index")
        else:
            if namespace.hard:
                reset_all_indexed_files_to_commit_state(fs, c)
                print(Fore.GREEN + "all indexed files were restored to their last recorded state")
            clean_index(fs, c)
            print(Fore.GREEN + "index was cleaned")
    else:
        clear_workspace(fs)
        expand_tree(get_last_tree_checksum(get_current_branch_path(fs, c), fs, c), fs, c)
        print(Fore.GREEN + "workspace was reset to last commit state")


def delete_indexed_changes(objects_to_reset: list, fs: AbstractFileSystem, c: Constants):
    for obj in objects_to_reset:
        if not fs.is_exist(obj):
            delete_indexed_changes_file(obj, fs, c)  # TODO so we can't reset indexed deleted directory
        elif fs.is_file(obj):
            delete_indexed_changes_file(obj, fs, c)
        else:
            delete_indexed_changes_dir(obj, fs, c)

    if len(indexed_paths) == 0:
        clean_index(fs, c)
    else:
        write_down_index(fs, c)


def delete_indexed_changes_file(file_path_absolute: str, fs: AbstractFileSystem, c: Constants):
    if file_path_absolute in indexed_paths:
        blob_index_path = f"{c.mygit_index_dir_path}/{indexed_paths.pop(file_path_absolute)}"
        if fs.is_exist(blob_index_path):
            fs.remove_file(blob_index_path)


def delete_indexed_changes_dir(dir_path_absolute: str, fs: AbstractFileSystem, c: Constants):
    for child in fs.get_directory_files(dir_path_absolute):
        if fs.is_file(child):
            delete_indexed_changes_file(child, fs, c)
        else:
            delete_indexed_changes_dir(child, fs, c)


def reset_to_commit_state(objects_to_reset: list, fs: AbstractFileSystem, c: Constants):
    for obj in objects_to_reset:
        if not obj.exists():
            reset_to_commit_state_file(obj, fs, c)  # TODO so we can't reset indexed deleted directory
        elif obj.is_file():
            reset_to_commit_state_file(obj, fs, c)
        else:
            reset_to_commit_state_dir(obj, fs, c)


def reset_to_commit_state_file(file_path_absolute: str, fs: AbstractFileSystem, c: Constants):
    if file_path_absolute in indexed_paths:
        if file_path_absolute in workspace_commit_state:
            expand_blob(workspace_commit_state[file_path_absolute], file_path_absolute, fs, c)
        else:
            fs.remove_file(file_path_absolute)


def reset_to_commit_state_dir(dir_path_absolute: str, fs: AbstractFileSystem, c: Constants):
    for child in fs.get_directory_files(dir_path_absolute):
        if fs.is_file(child):
            reset_to_commit_state_file(child, fs, c)
        else:
            reset_to_commit_state_dir(child, fs, c)


def reset_all_indexed_files_to_commit_state(fs: AbstractFileSystem, c: Constants):
    for path in indexed_paths:
        reset_to_commit_state_file(path, fs, c)


#=================================Status========================================
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


def print_status(fs: AbstractFileSystem, c: Constants):
    print("On branch " + get_current_branch_name(fs, c))

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


def check_blob(file_path: str, fs: AbstractFileSystem):
    source = fs.get_file_content_binary(file_path)
    content = compress(source, -1)
    checksum = sha1(content).hexdigest()
    message = "modified: " + file_path

    if file_path in workspace_commit_state and workspace_commit_state[file_path] == checksum:
        return

    if file_path in indexed_paths:
        status_indexed_paths.append(message)
        if not indexed_paths[file_path] == checksum:
            status_indexed_but_changed_paths.append(message)
    else:
        status_not_indexed_paths.append(message)


def check_tree(dir_path: str, fs: AbstractFileSystem):
    for child in fs.get_directory_files(dir_path):
        if child not in ignored_paths:
            if fs.is_file(child):
                check_blob(child, fs)
            else:
                check_tree(child, fs)


def check_deleted_files(fs: AbstractFileSystem):
    for path in workspace_commit_state:
        if not fs.is_exist(path):
            message = f"deleted: {path}"
            if path not in indexed_paths:
                status_not_indexed_paths.append(message)
            else:
                status_indexed_paths.append(message)


def print_ignored_paths():
    print(Fore.YELLOW + "ignored paths:")
    for ignored in ignored_paths:
        print(ignored)


def print_indexed_paths():
    if len(indexed_paths) == 0:
        print(Fore.YELLOW + "index is empty, use index <file1, file2, ...> to index changes")
    else:
        print(Fore.RESET + "indexed paths:")
        for path in indexed_paths:
            print(Fore.GREEN + path + " " + indexed_paths[path])


#================================Index==========================================
def handle_index(namespace: argparse.Namespace):
    if namespace.all:
        index_all_changes()
    elif len(namespace.files) > 0:
        index_input_files(namespace.files)
    else:
        print(Fore.YELLOW + "use index -a or index <file1, file2, ...> to index changes")


def index_all_changes(fs: AbstractFileSystem, c: Constants):
    for child in fs.get_directory_files("."):
        index_object(child, fs, c)
    index_deleted_files()
    write_down_index(fs, c)


def index_input_files(files: list, fs: AbstractFileSystem, c: Constants):
    if len(files) == 0:
        print(Fore.YELLOW + "you didn't mention any file")
    else:
        for file in files:
            index_object(file, fs, c)
        write_down_index(fs, c)


def index_object(file_path: str, fs: AbstractFileSystem, c: Constants):
    if not fs.is_exist(file_path) and file_path not in workspace_commit_state:
        print(Fore.RED + "file or directory doesn't exist: " + file_path)
    elif file_path in ignored_paths:
        print(Fore.YELLOW + "file has been ignored: " + file_path)
    else:
        if not fs.is_exist(file_path):  # TODO so we can't index deleted directory
            index_file(file_path, fs, c)
        elif fs.is_file(file_path):
            index_file(file_path, fs, c)
        else:
            index_tree(file_path, fs, c)


def index_tree(dir_path_absolute: str, fs: AbstractFileSystem, c: Constants):
    for child in fs.get_directory_files(dir_path_absolute):
        if child not in ignored_paths:
            if fs.is_file(child):
                index_file(child, fs, c)
            else:
                index_tree(child, fs, c)


def index_file(file_path_absolute: str, fs: AbstractFileSystem, c: Constants):
    if not fs.is_exist(file_path_absolute):
        indexed_paths[file_path_absolute] = "deleted"
        return

    source = fs.get_file_content_binary(file_path_absolute)
    content = compress(source, -1)
    checksum = sha1(content).hexdigest()
    blob_path = f"{c.mygit_objects_path}/{checksum}"
    blob_index_path = f"{c.mygit_index_dir_path}/{checksum}"

    if file_path_absolute in workspace_commit_state and workspace_commit_state[file_path_absolute] == checksum:
        return

    if file_path_absolute in indexed_paths:
        previous_indexed_checksum = indexed_paths[file_path_absolute]
        p_i_c_path = f"{c.mygit_index_dir_path}/{previous_indexed_checksum}"
        if previous_indexed_checksum != checksum and fs.is_exist(p_i_c_path):
            fs.remove_file(p_i_c_path)

    indexed_paths[file_path_absolute] = checksum
    if not fs.is_exist(blob_index_path) and not fs.is_exist(blob_path):
        fs.write_file_binary(blob_index_path, content)


def index_deleted_files():
    for path in workspace_commit_state:
        if not path.exists() and path not in indexed_paths:
            indexed_paths[path] = "deleted"


#================================Log============================================
def handle_log(namespace: argparse.Namespace):
    print_function = print_commit_content_oneline if namespace.oneline else print_commit_content
    commit_checksum = get_last_commit_checksum(get_current_branch_path())
    while commit_checksum != "":
        commit_content = get_commit_content(commit_checksum)
        print_function(commit_checksum, commit_content)
        commit_checksum = get_commit_parent_commit(commit_content)


def get_commit_content(commit_checksum: str, fs: AbstractFileSystem, c: Constants):
    return get_compressed_file_content(f"{c.mygit_objects_path}/{commit_checksum}", fs).split("\n")


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


#==================================Print========================================
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


#==================================Main=========================================
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
