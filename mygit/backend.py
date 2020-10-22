import logging
from colorama import Fore
from hashlib import sha1
from mygit.constants import Constants
from mygit.state import State
from pathlib import Path
from time import strftime
from zlib import decompress, compress


def is_init(c: Constants):
    mygit_files = c.__dict__
    for file_name in mygit_files:
        if len(file_name) > 5 and file_name[:5] == "mygit" and not mygit_files[file_name].exists():
            return False

    return True


def has_collisions_with_service_files(c: Constants) -> bool:
    colliding_files = 0
    mygit_files = c.__dict__
    for file_name in mygit_files:
        if len(file_name) > 5 and file_name[:5] == "mygit" and mygit_files[file_name].exists():
            logging.error(Fore.RED + f"file {file_name} prevent mygit from creating a repository, rename or delete it")
            colliding_files += 1

    return colliding_files != 0


def write_down_index(c: Constants, s: State):
    result = list()
    for path in s.current_indexed_paths:
        result.append(f"{path.relative_to(c.workspace_path)} {s.current_indexed_paths[path]}")
    content = compress(bytes("\n".join(result), encoding="utf-8"), -1)
    with Path.open(c.mygit_index_path, "wb") as index:
        index.write(content)


def clean_index(c: Constants):
    for child in c.mygit_index_dir_path.iterdir():
        Path.unlink(child)
    Path.open(c.mygit_index_path, "w").close()


def write_down_workspace_state(workspace_state: dict, c: Constants):
    result = list()
    for path in workspace_state:
        result.append(f"{path.relative_to(c.workspace_path)} {workspace_state[path]}")
    content = compress(bytes("\n".join(result), encoding="utf-8"), -1)
    checksum = sha1(content).hexdigest()
    with Path.open(c.mygit_objects_path / checksum, "wb") as workspace_state_file:
        workspace_state_file.write(content)

    return checksum


def clear_workspace(c: Constants, s: State):
    for child in c.workspace_path.iterdir():
        if child not in s.ignored_paths:
            if child.is_file():
                Path.unlink(child)
            else:
                clear_directory(child, s)


def clear_directory(directory_path: Path, s: State):
    for child in directory_path.iterdir():
        if child not in s.ignored_paths:
            if child.is_file():
                Path.unlink(child)
            else:
                clear_directory(child, s)
    directory_path.rmdir()


def get_tree_content(saved_tree_checksum: str, c: Constants):
    content = dict()
    if saved_tree_checksum == "":
        return content

    saved_tree = get_compressed_file_content(c.mygit_objects_path / saved_tree_checksum).split("\n")
    for obj in saved_tree:
        buffer = obj.split()
        object_type = buffer[0]
        path = c.workspace_path / buffer[1]
        checksum = buffer[2]

        if object_type not in content:
            content[object_type] = {path: checksum}
        elif path not in content[object_type]:
            content[object_type][path] = checksum
        else:
            logging.critical(Fore.RED + f"path appears more than ones: {path} whole tree: {saved_tree}")

    return content


def get_last_tree_checksum(branch_path: Path, c: Constants):
    last_commit_path = c.mygit_objects_path / get_last_commit_checksum(branch_path)
    return get_tree_checksum(last_commit_path)


def get_tree_checksum(commit_path: Path):
    return get_compressed_file_content(commit_path).split("\n")[0]


def get_current_branch_name(c: Constants):
    with Path.open(c.mygit_head_path, "r") as head:
        current_branch_name = head.read()
    return current_branch_name


def get_current_branch_path(c: Constants):
    return c.mygit_branches_path / get_current_branch_name(c)


def get_last_commit_checksum(branch_path: Path):
    with Path.open(branch_path, "r") as branch:
        last_commit_checksum = branch.read()
    return last_commit_checksum


def get_last_commit_index_content(c: Constants):
    last_commit_checksum = get_last_commit_checksum(get_current_branch_path(c))
    if last_commit_checksum == "":
        return ""
    commit_content = get_commit_content(last_commit_checksum, c)
    content_checksum = commit_content[1]
    return get_compressed_file_content(c.mygit_objects_path / content_checksum)


def get_compressed_file_content(file_path_absolute: Path):
    if file_path_absolute.stat().st_size == 0:
        return ""
    with Path.open(file_path_absolute, "rb") as file:
        content = decompress(file.read()).decode()
    return content


# ===Commit=============================================================================================================
def make_commit(commit_message: str, c: Constants, s: State):
    if not has_uncommitted_changes(c, s):
        logging.warning(Fore.YELLOW + "working tree is clean, you can't commit if there's no changes")
    elif len(s.status_indexed_paths) == 0:
        logging.warning(
            Fore.YELLOW + "you can't commit if your index is empty, use index <file1, file2, ...> to index changes")
    else:
        current_branch_path = get_current_branch_path(c)
        last_commit_checksum = get_last_commit_checksum(current_branch_path)
        create_commit(current_branch_path, commit_message, last_commit_checksum, c, s)


def create_commit(current_branch_path: Path, commit_message: str, parent_commit_checksum: str, c: Constants, s: State):
    new_workspace_state = dict()
    current_tree_checksum = create_tree(c.workspace_path, new_workspace_state, c, s)
    workspace_state_checksum = write_down_workspace_state(new_workspace_state, c)
    content_raw = bytes(
        current_tree_checksum + "\n" +
        workspace_state_checksum + "\n" +
        commit_message + "\n" +
        str(strftime("%c %z")) + "\n" +
        parent_commit_checksum, encoding="utf-8")
    content = compress(content_raw, -1)
    checksum = sha1(content).hexdigest()
    commit_path = c.mygit_objects_path / checksum
    with Path.open(commit_path, "wb") as commit:
        commit.write(content)
    with Path.open(current_branch_path, "w") as branch:
        branch.write(checksum)
    clean_index(c)


def create_tree(dir_path: Path, new_workspace_state: dict, c: Constants, s: State):
    tree_objects = []
    for child in dir_path.iterdir():
        if child in s.ignored_paths:
            continue
        if child.is_file():
            blob_checksum = create_blob(child, c, s)
            if blob_checksum is not None:
                tree_objects.append(f"blob {child.relative_to(c.workspace_path)} {blob_checksum}")
                new_workspace_state[child] = blob_checksum
        else:
            tree_checksum = create_tree(child, new_workspace_state, c, s)
            if tree_checksum is not None:
                tree_objects.append(f"tree {child.relative_to(c.workspace_path)} {tree_checksum}")

    if len(tree_objects) == 0:
        return None
    content_raw = bytes("\n".join(tree_objects), encoding="utf-8")
    content = compress(content_raw, -1)
    checksum = sha1(content).hexdigest()
    tree_path = c.mygit_objects_path / checksum
    if not tree_path.exists():
        with Path.open(tree_path, "wb") as tree:
            tree.write(content)

    return checksum


def create_blob(file_path: Path, c: Constants, s: State):
    if file_path in s.current_indexed_paths:
        indexed_checksum = s.current_indexed_paths[file_path]
        indexed_blob_path = c.mygit_index_dir_path / indexed_checksum
        if indexed_blob_path.exists():
            indexed_blob_path.rename(c.mygit_objects_path / indexed_checksum)
        return indexed_checksum
    elif file_path in s.last_commit_indexed_path:
        return s.last_commit_indexed_path[file_path]

    return None


# ===Checkout===========================================================================================================
def checkout_to_branch(branch_name, c: Constants, s: State):
    branch_path = c.mygit_branches_path / branch_name
    if not branch_path.exists():
        logging.error(Fore.RED + f"branch {branch_name} doesn't exist")
    elif has_uncommitted_changes(c, s):
        logging.error(Fore.RED + "you can't checkout with uncommitted changes, use commit or reset")  # TODO reset
    else:
        clear_workspace(c, s)
        expand_tree(get_last_tree_checksum(branch_path, c), c)

        with Path.open(c.mygit_head_path, "w") as head:
            head.write(branch_name)
        logging.info(Fore.GREEN + f"moved to branch {branch_name}")


def create_new_branch_from_current_and_checkout(new_branch_name: str, c: Constants):
    create_new_branch_from_current(new_branch_name, c)
    with Path.open(c.mygit_head_path, "w") as head:
        head.write(new_branch_name)
    logging.info(Fore.GREEN + f"moved to new branch {new_branch_name}")


def expand_tree(tree_checksum: str, c: Constants):
    tree_content = get_tree_content(tree_checksum, c)
    for obj_type in tree_content:
        if obj_type == "blob":
            for path in tree_content[obj_type]:
                expand_blob(tree_content[obj_type][path], path, c)
        else:
            for path in tree_content[obj_type]:
                Path.mkdir(path)
                expand_tree(tree_content[obj_type][path], c)


def expand_blob(blob_checksum: str, target_filename: Path, c: Constants):
    with Path.open(c.mygit_objects_path / blob_checksum, "rb") as source:
        content = decompress(source.read())

    with Path.open(target_filename, "wb") as file:
        file.write(content)


# ===Branch=============================================================================================================
def remove_branch(branch_name: str, c: Constants):
    branch_path = c.mygit_branches_path / branch_name
    if branch_name == get_current_branch_name(c):
        logging.warning(Fore.YELLOW + "you can't remove the branch, on which you are. Checkout to another branch first")
    elif not branch_path.exists():
        logging.error(Fore.RED + "branch doesn't exist")
    else:
        with Path.open(branch_path, "r") as branch:
            commit_checksum = branch.read()
        Path.unlink(branch_path)
        logging.info(Fore.GREEN + f"Deleted branch {branch_name} ({commit_checksum})")


def create_new_branch_from_current(new_branch_name: str, c: Constants):
    current_branch_path = get_current_branch_path(c)
    last_commit = get_last_commit_checksum(current_branch_path)
    create_new_branch_from_commit(new_branch_name, last_commit, c)


def create_new_branch_from_commit(branch_name: str, commit_checksum: str, c: Constants):
    branch_path = c.mygit_branches_path / branch_name
    commit_path = c.mygit_objects_path / commit_checksum
    if branch_path.exists():
        logging.warning(Fore.YELLOW + f"branch {branch_name} already exists")
    elif not commit_path.exists():
        logging.error(Fore.RED + "commit doesn't exist")
    else:
        with Path.open(branch_path, "w") as new_branch:
            new_branch.write(commit_checksum)
        logging.info(Fore.GREEN + f"new branch {branch_name} is created")


def show_branches(c: Constants):
    logging.info("branches:")
    for branch_path in c.mygit_branches_path.iterdir():
        logging.warning(Fore.YELLOW + str(branch_path.relative_to(c.mygit_branches_path)))


# ===Merge==============================================================================================================
def merge(branch_name: str, c: Constants, s: State):
    branch_path = c.mygit_branches_path / branch_name
    current_branch_name = get_current_branch_name(c)
    current_branch_path = c.mygit_branches_path / current_branch_name

    if not branch_path.exists():
        logging.error(Fore.RED + f"branch {branch_name} doesn't exist")
    else:
        from_commit_checksum = get_last_commit_checksum(current_branch_path)
        to_commit_checksum = get_last_commit_checksum(branch_path)
        if from_commit_checksum == to_commit_checksum:
            logging.error(
                Fore.RED + f"You can't merge {current_branch_name} with {branch_name}\n"
                           f"Branches are pointing on the same commit")
        elif has_uncommitted_changes(c, s):
            logging.error(Fore.RED + "you can't merge with uncommitted changes, use commit or reset")  # TODO reset
        elif can_be_fast_forwarded(from_commit_checksum, to_commit_checksum, c):
            clear_workspace(c, s)
            expand_tree(get_tree_checksum(c.mygit_objects_path / to_commit_checksum), c)

            with Path.open(current_branch_path, "w") as current_branch:
                current_branch.write(to_commit_checksum)

            logging.info(Fore.GREEN + f"merged {branch_name} into current branch")
            logging.info(Fore.RESET + f"you can safely delete branch {branch_name} with branch -r {branch_name}")
        else:
            logging.error(Fore.RED + "Possible merging conflicts, fast-forward is impossible")


def can_be_fast_forwarded(from_commit_checksum: str, to_commit_checksum: str, c: Constants):
    commit_checksum = to_commit_checksum

    while commit_checksum != "":
        if commit_checksum == from_commit_checksum:
            return True
        commit_content = get_commit_content(commit_checksum, c)
        commit_checksum = get_commit_parent_commit(commit_content)
    return False


# ===Reset==============================================================================================================
def delete_indexed_changes(objects_to_reset: list, c: Constants, s: State):
    for obj in objects_to_reset:
        object_path = c.workspace_path / obj
        if not object_path.exists():
            delete_indexed_changes_file(object_path, c, s)  # TODO so we can't reset indexed deleted directory
        elif object_path.is_file():
            delete_indexed_changes_file(object_path, c, s)
        else:
            delete_indexed_changes_dir(object_path, c, s)

    if len(s.current_indexed_paths) == 0:
        clean_index(c)
    else:
        write_down_index(c, s)


def delete_indexed_changes_file(file_path_absolute: Path, c: Constants, s: State):
    if file_path_absolute in s.current_indexed_paths:
        blob_index_path = c.mygit_index_dir_path / s.current_indexed_paths.pop(file_path_absolute)
        if blob_index_path.exists():
            Path.unlink(blob_index_path)


def delete_indexed_changes_dir(dir_path_absolute: Path, c: Constants, s: State):
    for child in dir_path_absolute.iterdir():
        if child.is_file():
            delete_indexed_changes_file(child, c, s)
        else:
            delete_indexed_changes_dir(child, c, s)


def reset_to_commit_state(objects_to_reset: list, c: Constants, s: State):
    for obj in objects_to_reset:
        object_path = c.workspace_path / obj
        if not object_path.exists():
            reset_to_commit_state_file(object_path, c, s)  # TODO so we can't reset indexed deleted directory
        elif object_path.is_file():
            reset_to_commit_state_file(object_path, c, s)
        else:
            reset_to_commit_state_dir(object_path, c, s)


def reset_to_commit_state_file(file_path_absolute: Path, c: Constants, s: State):
    if file_path_absolute in s.current_indexed_paths:
        if file_path_absolute in s.last_commit_indexed_path:
            expand_blob(s.last_commit_indexed_path[file_path_absolute], file_path_absolute, c)
        else:
            Path.unlink(file_path_absolute)


def reset_to_commit_state_dir(dir_path_absolute: Path, c: Constants, s: State):
    for child in dir_path_absolute.iterdir():
        if child.is_file():
            reset_to_commit_state_file(child, c, s)
        else:
            reset_to_commit_state_dir(child, c, s)


def reset_all_indexed_files_to_commit_state(c: Constants, s: State):
    for path in s.current_indexed_paths:
        reset_to_commit_state_file(path, c, s)


# ===Status=============================================================================================================
def has_uncommitted_changes(c: Constants, s: State):
    check_status(c, s)
    return len(s.status_indexed_paths) + len(s.status_not_indexed_paths) > 0


def check_status(c: Constants, s: State):
    if not s.status_is_checked:
        check_tree(c.workspace_path, c, s)
        check_deleted_files(c, s)
        s.status_is_checked = True


def print_status(c: Constants, s: State):
    logging.info(f"On branch {get_current_branch_name(c)}")

    if not has_uncommitted_changes(c, s):
        logging.info("nothing to commit, working tree is clean")

    if len(s.status_indexed_paths) > 0:
        logging.info(Fore.RESET + "indexed changes:")
        for indexed in s.status_indexed_paths:
            logging.info(Fore.GREEN + indexed)

    if len(s.status_not_indexed_paths) > 0:
        logging.info(Fore.RESET + "not indexed changes:")
        for not_indexed in s.status_not_indexed_paths:
            logging.info(Fore.RED + not_indexed)

    if len(s.status_indexed_but_changed_paths) > 0:
        logging.info(Fore.RESET + "indexed files with new not indexed changes:")
        for indexed in s.status_indexed_but_changed_paths:
            logging.warning(Fore.YELLOW + indexed)


def check_blob(file_path: Path, c: Constants, s: State):
    with Path.open(file_path, "rb") as source:
        content = compress(source.read(), -1)
        checksum = sha1(content).hexdigest()
        relative_path = str(file_path.relative_to(c.workspace_path))
        message = "modified: " + relative_path

    if file_path in s.last_commit_indexed_path and s.last_commit_indexed_path[file_path] == checksum:
        return

    if file_path in s.current_indexed_paths:
        s.status_indexed_paths.append(message)
        if not s.current_indexed_paths[file_path] == checksum:
            s.status_indexed_but_changed_paths.append(message)
    else:
        s.status_not_indexed_paths.append(message)


def check_tree(dir_path: Path, c: Constants, s: State):
    for child in dir_path.iterdir():
        if child not in s.ignored_paths:
            if child.is_file():
                check_blob(child, c, s)
            else:
                check_tree(child, c, s)


def check_deleted_files(c: Constants, s: State):
    for path in s.last_commit_indexed_path:
        if not path.exists():
            message = "deleted: " + str(path.relative_to(c.workspace_path))
            if path not in s.current_indexed_paths:
                s.status_not_indexed_paths.append(message)
            else:
                s.status_indexed_paths.append(message)


def print_ignored_paths(c: Constants, s: State):
    logging.warning(Fore.YELLOW + "ignored paths:")
    for ignored in s.ignored_paths:
        logging.info(str(ignored.relative_to(c.workspace_path)))


def print_indexed_paths(c: Constants, s: State):
    if len(s.current_indexed_paths) == 0:
        logging.warning(Fore.YELLOW + "index is empty, use index <file1, file2, ...> to index changes")
    else:
        logging.info(Fore.RESET + "indexed paths:")
        for path in s.current_indexed_paths:
            logging.info(Fore.GREEN + f"{path.relative_to(c.workspace_path)} {s.current_indexed_paths[path]}")


# ===Index==============================================================================================================
def index_all_changes(c: Constants, s: State):
    for child in c.workspace_path.iterdir():
        index_object(child, c, s)
    index_deleted_files(s)
    write_down_index(c, s)


def index_input_files(files: list, c: Constants, s: State):
    if len(files) == 0:
        logging.warning(Fore.YELLOW + "you didn't mention any file")
    else:
        for file in files:
            index_object(c.workspace_path / file, c, s)
        write_down_index(c, s)


def index_object(file_path_absolute: Path, c: Constants, s: State):
    file_path_relative = str(file_path_absolute.relative_to(c.workspace_path))
    if not file_path_absolute.exists() and file_path_absolute not in s.last_commit_indexed_path:
        logging.error(Fore.RED + f"file or directory doesn't exist: {file_path_relative}")
    elif file_path_absolute in s.ignored_paths:
        logging.warning(Fore.YELLOW + f"file has been ignored: {file_path_relative}")
    else:
        if not file_path_absolute.exists():  # TODO so we can't index deleted directory
            index_file(file_path_absolute, c, s)
        elif file_path_absolute.is_file():
            index_file(file_path_absolute, c, s)
        else:
            index_tree(file_path_absolute, c, s)


def index_tree(dir_path_absolute: Path, c: Constants, s: State):
    for child in dir_path_absolute.iterdir():
        if child not in s.ignored_paths:
            if child.is_file():
                index_file(child, c, s)
            else:
                index_tree(child, c, s)


def index_file(file_path_absolute: Path, c: Constants, s: State):
    if not file_path_absolute.exists():
        s.current_indexed_paths[file_path_absolute] = "deleted"
        return

    with Path.open(file_path_absolute, "rb") as source:
        content = compress(source.read(), -1)
        checksum = sha1(content).hexdigest()
        blob_path = c.mygit_objects_path / checksum
        blob_index_path = c.mygit_index_dir_path / checksum

    if file_path_absolute in s.last_commit_indexed_path and s.last_commit_indexed_path[file_path_absolute] == checksum:
        return

    if file_path_absolute in s.current_indexed_paths:
        previous_indexed_checksum = s.current_indexed_paths[file_path_absolute]
        p_i_c_path = c.mygit_index_dir_path / previous_indexed_checksum
        if previous_indexed_checksum != checksum and p_i_c_path.exists():
            Path.unlink(p_i_c_path)

    s.current_indexed_paths[file_path_absolute] = checksum
    if not blob_index_path.exists() and not blob_path.exists():
        with Path.open(blob_index_path, "wb") as blob:
            blob.write(content)


def index_deleted_files(s: State):
    for path in s.last_commit_indexed_path:
        if not path.exists() and path not in s.current_indexed_paths:
            s.current_indexed_paths[path] = "deleted"


# ===Log================================================================================================================
def get_commit_content(commit_checksum: str, c: Constants):
    return get_compressed_file_content(c.mygit_objects_path / commit_checksum).split("\n")


def get_commit_parent_commit(commit_content: list):
    return commit_content[4]


def print_commit_content(commit_checksum: str, content: list):
    logging.info(Fore.YELLOW + f"commit: {commit_checksum}\n" +
                 Fore.RESET + f"date: {content[3]}\n"
                              f"message:\n\n"
                              f"    {content[2]}\n")


def print_commit_content_oneline(commit_checksum: str, content: list):
    logging.info(Fore.YELLOW + commit_checksum + " " + Fore.RESET + content[2])


def print_internal_log(c: Constants):
    with Path.open(c.mygit_log_path, "r") as obj:
        content = obj.read()
    logging.info(content + "\n")


# ===Print==============================================================================================================
def print_compressed_object(checksum: str, c: Constants):
    object_path = c.mygit_objects_path / checksum
    if not object_path.exists():
        logging.error(Fore.RED + "object doesn't exist")
        return
    logging.info(get_compressed_file_content(object_path) + "\n")
