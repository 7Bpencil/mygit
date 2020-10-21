from abc import ABC, abstractmethod


class AbstractFileSystem(ABC):
    @abstractmethod
    def create_directory(self, directory_path: str):
        pass

    @abstractmethod
    def remove_directory(self, directory_path: str):
        pass

    @abstractmethod
    def create_file(self, file_path: str):
        pass

    @abstractmethod
    def remove_file(self, file_path: str):
        pass

    @abstractmethod
    def is_exist(self, file_or_directory_path: str) -> bool:
        pass

    @abstractmethod
    def write_file_binary(self, file_path: str, content: bytes):
        pass

    @abstractmethod
    def write_file_text(self, file_path: str, content: str):
        pass

    @abstractmethod
    def get_file_content_binary(self, file_path: str) -> bytes:
        pass

    @abstractmethod
    def get_file_content_text(self, file_path: str) -> str:
        pass

    @abstractmethod
    def read_lines(self, file_path: str) -> list:
        pass

    @abstractmethod
    def get_directory_files(self, directory_path: str) -> list:
        pass

    @abstractmethod
    def is_file(self, file_path: str) -> bool:
        pass

    @abstractmethod
    def rename_file(self, original_file_path: str, target_file_path: str):
        pass

    @abstractmethod
    def file_is_empty(self, file_path: str) -> bool:
        pass
