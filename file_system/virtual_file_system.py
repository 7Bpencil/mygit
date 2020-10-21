from file_system.abstract_file_system import AbstractFileSystem


class VirtualFileSystem(AbstractFileSystem):
    """We try to mimic os module. So we will recreate exceptions too.
       We will assume that:
       File is a pair [path : content] where path is a string and content is a string or bytes.
       Directory is a pair [path : None] where path is a string"""

    def __init__(self):
        self.__files = {}

    def create_directory(self, directory_path: str):
        if self.is_exist(directory_path):
            raise FileExistsError(f"file or directory {directory_path} already exists")

        if not self.__is_parent_directory_exist(directory_path):
            raise PermissionError(f"Cannot create directory because "
                                  f"there is no parent directory for a {directory_path}")

        self.__files[directory_path] = None

    def remove_directory(self, directory_path: str):
        if not self.is_exist(directory_path):
            raise FileNotFoundError(f"file or directory {directory_path} does not exist")

        if self.is_file(directory_path):
            raise NotADirectoryError(f"{directory_path} is not a directory")

        for path in self.__files:
            if directory_path in path and path != directory_path:
                raise PermissionError(f"directory {directory_path} is not empty")

        del self.__files[directory_path]

    def create_file(self, file_path: str):
        self.write_file_text(file_path, "")

    def remove_file(self, file_path: str):
        if not self.is_exist(file_path):
            raise FileNotFoundError(f"file or directory {file_path} does not exist")

        if not self.is_file(file_path):
            raise IsADirectoryError(f"{file_path} is not a file")

        del self.__files[file_path]

    def is_exist(self, file_or_directory_path: str) -> bool:
        return file_or_directory_path in self.__files

    def write_file_binary(self, file_path: str, content: bytes):
        self.__write_file(file_path, content)

    def write_file_text(self, file_path: str, content: str):
        self.__write_file(file_path, content)

    def __write_file(self, file_path: str, content):
        if self.is_exist(file_path):
            if self.is_file(file_path):
                self.__files[file_path] = content
            else:
                raise IsADirectoryError(f"{file_path} is not a file. You cannot write to a directory")

        elif self.__is_parent_directory_exist(file_path):
            self.__files[file_path] = content
        else:
            raise PermissionError(f"File {file_path} does not exist. "
                                  f"Cannot create new one because there is no parent directory for a file")

    def get_file_content_binary(self, file_path: str) -> bytes:
        return self.__get_file_content(file_path, self.__convert_to_bytes)

    def get_file_content_text(self, file_path: str) -> str:
        return self.__get_file_content(file_path, self.__convert_to_string)

    def __get_file_content(self, file_path: str, content_converter):
        if not self.is_exist(file_path):
            raise FileNotFoundError(f"file or directory {file_path} does not exist")

        if not self.is_file(file_path):
            raise IsADirectoryError(f"{file_path} is not a file")

        return content_converter(self.__files[file_path])

    def read_lines(self, file_path: str) -> list:
        buffer = self.get_file_content_text(file_path)
        lines_raw = buffer.split("\n")
        for i in range(len(lines_raw)):
            lines_raw[i] += "\n"
        return lines_raw

    def get_directory_files(self, directory_path: str) -> list:
        if not self.is_exist(directory_path):
            raise FileNotFoundError(f"file or directory {directory_path} does not exist")

        if self.is_file(directory_path):
            raise NotADirectoryError(f"{directory_path} is not a directory")

        target_hierarchy_length = self.__get_hierarchy_length(directory_path) + 1

        files_path = set()
        for path in self.__files:
            if directory_path in path and self.__get_hierarchy_length(path) == target_hierarchy_length:
                files_path.add(self.__get_file_name(path))

        return list(files_path)

    def is_file(self, file_path: str) -> bool:
        if not self.is_exist(file_path):
            raise FileNotFoundError(f"file or directory {file_path} does not exist")

        return self.__files[file_path] is not None

    def rename_file(self, original_file_path: str, target_file_path: str):
        if self.is_exist(target_file_path):
            raise FileExistsError(f"file or directory {target_file_path} already exists")
        content = self.get_file_content_binary(original_file_path)
        self.write_file_binary(target_file_path, content)
        self.remove_file(original_file_path)

    def file_is_empty(self, file_path: str) -> bool:
        return len(self.get_file_content_text(file_path)) == 0

    def __is_parent_directory_exist(self, file_path) -> bool:
        parent_dir = self.__get_parent_directory(file_path)
        if len(parent_dir) == 0:  # It means that directory or file is in root directory
            return True
        return self.is_exist(parent_dir) and self.__is_parent_directory_exist(parent_dir)

    @staticmethod
    def __convert_to_bytes(content):
        return bytes(content, encoding="utf-8") if isinstance(content, str) else content

    @staticmethod
    def __convert_to_string(content):
        return content if isinstance(content, str) else content.decode("utf-8")

    @staticmethod
    def __get_hierarchy(path) -> list:
        return str.split(path, "/")

    def __get_hierarchy_length(self, path) -> int:
        return len(self.__get_hierarchy(path))

    @staticmethod
    def __get_file_name(path) -> str:
        last_slash_index = str.rfind(path, "/")
        return path[(last_slash_index + 1):]

    @staticmethod
    def __get_parent_directory(path) -> str:
        last_slash_index = str.rfind(path, "/")
        return path[:(last_slash_index if last_slash_index != -1 else 0)]
