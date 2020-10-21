from file_system.abstract_file_system import AbstractFileSystem
import os


class FileSystem(AbstractFileSystem):
    """I chose not to check errors because os module does it for me"""

    def create_directory(self, directory_path: str):
        os.mkdir(directory_path)

    def remove_directory(self, directory_path: str):
        os.rmdir(directory_path)

    def create_file(self, file_path: str):
        open(file_path, "w").close()

    def remove_file(self, file_path: str):
        os.remove(file_path)

    def is_exist(self, file_or_directory_path: str) -> bool:
        return os.path.exists(file_or_directory_path)

    def write_file_binary(self, file_path: str, content: bytes):
        with open(file_path, "wb") as file_handler:
            file_handler.write(content)

    def write_file_text(self, file_path: str, content: str):
        with open(file_path, "w") as file_handler:
            file_handler.write(content)

    def get_file_content_binary(self, file_path: str) -> bytes:
        with open(file_path, "rb") as file_handler:
            binary_data = file_handler.read()
        return binary_data

    def get_file_content_text(self, file_path: str) -> str:
        with open(file_path, "r") as file_handler:
            text_data = file_handler.read()
        return text_data

    def read_lines(self, file_path: str) -> list:
        with open(file_path, "r") as file_handler:
            lines = file_handler.readlines()
        return lines

    def get_directory_files(self, directory_path: str) -> list:
        return os.listdir(directory_path)

    def is_file(self, file_path: str) -> bool:
        return os.path.isfile(file_path)

    def rename_file(self, original_file_path: str, target_file_path: str):
        os.rename(original_file_path, target_file_path)

    def file_is_empty(self, file_path: str) -> bool:
        return os.stat(file_path).st_size == 0
