from file_system.virtual_file_system import VirtualFileSystem
import pytest


class TestVirtualFileSystem:  # TODO test through comparison with os
    @classmethod
    def setup_class(cls):
        cls.file_system = VirtualFileSystem()

    def reset_file_system(self):
        files = self.file_system.__dict__['_VirtualFileSystem__files']
        files.clear()

        """
        hello.py
        images:
            forest.png
            house.png
            cars:
                6.jpg
            boats:
                (empty directory)
            future.png (empty file)
        """

        files["hello.py"] = "print('HelloWorld!')"
        files["images"] = None
        files["images/forest.png"] = b'some_picture'
        files["images/house.png"] = b'another_picture'
        files["images/cars"] = None
        files["images/cars/6.jpg"] = b'masterpiece'
        files["images/boats"] = None
        files["images/future.png"] = ""

    def setup_method(self, method):
        self.reset_file_system()

    def test_create_directory_that_already_exist(self):
        with pytest.raises(FileExistsError):
            self.file_system.create_directory("images")
        with pytest.raises(FileExistsError):
            self.file_system.create_directory("images/cars")

    def test_create_directory_with_wrong_path(self):
        with pytest.raises(PermissionError):
            self.file_system.create_directory("images/helicopters/old")
        with pytest.raises(PermissionError):
            self.file_system.create_directory("music/rock")

    def test_create_directory_successfully(self):
        directory = "images/helicopters"
        assert not self.file_system.is_exist(directory)
        self.file_system.create_directory(directory)
        assert self.file_system.is_exist(directory) and not self.file_system.is_file(directory)

    def test_remove_directory_that_doesnt_exist(self):
        with pytest.raises(FileNotFoundError):
            self.file_system.remove_directory("music")
        with pytest.raises(FileNotFoundError):
            self.file_system.remove_directory("images/helicopter.png")

    def test_remove_directory_that_is_a_file(self):
        with pytest.raises(NotADirectoryError):
            self.file_system.remove_directory("hello.py")
        with pytest.raises(NotADirectoryError):
            self.file_system.remove_directory("images/cars/6.jpg")

    def test_remove_directory_that_has_files(self):
        with pytest.raises(PermissionError):
            self.file_system.remove_directory("images")
        with pytest.raises(PermissionError):
            self.file_system.remove_directory("images/cars")

    def test_remove_directory_successfully(self):
        directory = "images/boats"
        assert self.file_system.is_exist(directory) and not self.file_system.is_file(directory)
        self.file_system.remove_directory(directory)
        assert not self.file_system.is_exist(directory)

    def test_remove_file_that_doesnt_exist(self):
        with pytest.raises(FileNotFoundError):
            self.file_system.remove_file("aaa.txt")

    def test_remove_file_that_is_directory(self):
        with pytest.raises(IsADirectoryError):
            self.file_system.remove_file("images/cars")

    def test_remove_file_successfully(self):
        file_path = "images/cars/6.jpg"
        assert self.file_system.is_exist(file_path)
        self.file_system.remove_file(file_path)
        assert not self.file_system.is_exist(file_path)

    def test_is_file_or_directory_exist_on_existing_files(self):
        assert self.file_system.is_exist("images/cars/6.jpg")
        assert self.file_system.is_exist("images")

    def test_is_file_or_directory_exist_on_not_existing_files(self):
        assert not self.file_system.is_exist("images/caars/6.jpg")
        assert not self.file_system.is_exist("hekko.py")

    def test_write_file_binary_to_directory(self):
        with pytest.raises(IsADirectoryError):
            self.file_system.write_file_binary("images", b'abc')

    def test_write_file_text_to_directory(self):
        with pytest.raises(IsADirectoryError):
            self.file_system.write_file_binary("images", b'abc')

    def test_write_file_binary_to_file_with_wrong_path(self):
        with pytest.raises(PermissionError):
            self.file_system.write_file_binary("images/helicopters/ah64.jpg", b'abc')

    def test_write_file_text_to_file_with_wrong_path(self):
        with pytest.raises(PermissionError):
            self.file_system.write_file_binary("images/helicopters/ah64.jpg", b'abc')

    def test_write_file_binary_to_new_file(self):
        file_path = "images/boats/my_one.png"
        content = b'abc'
        assert not self.file_system.is_exist(file_path)
        self.file_system.write_file_binary(file_path, content)
        assert self.file_system.is_exist(file_path) and self.file_system.is_file(file_path)
        assert content == self.file_system.get_file_content_binary(file_path)

    def test_write_file_text_to_new_file(self):
        file_path = "images/boats/my_one.png"
        content = 'abc'
        assert not self.file_system.is_exist(file_path)
        self.file_system.write_file_text(file_path, content)
        assert self.file_system.is_exist(file_path) and self.file_system.is_file(file_path)
        assert content == self.file_system.get_file_content_text(file_path)

    def test_write_file_binary_to_existing_file(self):
        file_path = "images/cars/6.jpg"
        content = self.file_system.get_file_content_binary(file_path) + b'additional_data'
        assert self.file_system.is_exist(file_path) and self.file_system.is_file(file_path)
        self.file_system.write_file_binary(file_path, content)
        assert self.file_system.is_exist(file_path) and self.file_system.is_file(file_path)
        assert content == self.file_system.get_file_content_binary(file_path)

    def test_write_file_text_to_existing_file(self):
        file_path = "images/cars/6.jpg"
        content = self.file_system.get_file_content_text(file_path) + "additional_data"
        assert self.file_system.is_exist(file_path) and self.file_system.is_file(file_path)
        self.file_system.write_file_text(file_path, content)
        assert self.file_system.is_exist(file_path) and self.file_system.is_file(file_path)
        assert content == self.file_system.get_file_content_text(file_path)

    def test_get_file_content_binary_on_not_existing_file(self):
        with pytest.raises(FileNotFoundError):
            self.file_system.get_file_content_binary("aaa.txt")

    def test_get_file_content_text_on_not_existing_file(self):
        with pytest.raises(FileNotFoundError):
            self.file_system.get_file_content_text("aaa.txt")

    def test_get_file_content_binary_on_directory(self):
        with pytest.raises(IsADirectoryError):
            self.file_system.get_file_content_binary("images/cars")

    def test_get_file_content_text_on_directory(self):
        with pytest.raises(IsADirectoryError):
            self.file_system.get_file_content_text("images/cars")

    def test_get_file_content_binary_file_was_binary(self):
        assert b'some_picture' == self.file_system.get_file_content_binary("images/forest.png")
        assert 'some_picture' != self.file_system.get_file_content_binary("images/forest.png")

    def test_get_file_content_binary_file_was_text(self):
        assert b"print('HelloWorld!')" == self.file_system.get_file_content_binary("hello.py")
        assert "print('HelloWorld!')" != self.file_system.get_file_content_binary("hello.py")

    def test_get_file_content_text_file_was_binary(self):
        assert b'some_picture' != self.file_system.get_file_content_text("images/forest.png")
        assert 'some_picture' == self.file_system.get_file_content_text("images/forest.png")

    def test_get_file_content_text_file_was_text(self):
        assert b"print('HelloWorld!')" != self.file_system.get_file_content_text("hello.py")
        assert "print('HelloWorld!')" == self.file_system.get_file_content_text("hello.py")

    def test_get_directory_files_not_existing_directory(self):
        with pytest.raises(FileNotFoundError):
            self.file_system.get_directory_files("images/carz")
        with pytest.raises(FileNotFoundError):
            self.file_system.get_directory_files("music")

    def test_get_directory_files_from_file(self):
        with pytest.raises(NotADirectoryError):
            self.file_system.get_directory_files("hello.py")
        with pytest.raises(NotADirectoryError):
            self.file_system.get_directory_files("images/house.png")

    def test_get_directory_on_directory_with_files(self):
        directory = "images"
        expected = {"forest.png", "house.png", "cars", "boats"}
        assert expected == set(self.file_system.get_directory_files(directory))

    def test_get_directory_on_empty_directory(self):
        directory = "images/boats"
        assert len(self.file_system.get_directory_files(directory)) == 0

    def test_is_file_on_not_existing_file_or_directory(self):
        with pytest.raises(FileNotFoundError):
            self.file_system.is_file("aaa.txt")
        with pytest.raises(FileNotFoundError):
            self.file_system.is_file("images/cars/hello.py")
        with pytest.raises(FileNotFoundError):
            self.file_system.is_file("images/carz")

    def test_is_file_on_existing_directory(self):
        assert not self.file_system.is_file("images/cars")
        assert not self.file_system.is_file("images")

    def test_is_file_on_existing_file(self):
        assert self.file_system.is_file("hello.py")
        assert self.file_system.is_file("images/forest.png")
        assert self.file_system.is_file("images/house.png")
        assert self.file_system.is_file("images/cars/6.jpg")

    def test_rename_on_not_existing_file(self):
        with pytest.raises(FileNotFoundError):
            self.file_system.rename_file("aaa.txt", "bbb.txt")

    def test_rename_on_directory(self):
        with pytest.raises(IsADirectoryError):
            self.file_system.rename_file("images", "pictures")

    def test_rename_to_existing_file(self):
        with pytest.raises(FileExistsError):
            self.file_system.rename_file("images/forest.png", "hello.py")

    def test_rename_to_wrong_path(self):
        with pytest.raises(PermissionError):
            self.file_system.rename_file("hello.py", "code/hello.py")

    def test_rename_successfully(self):
        old_name = "hello.py"
        new_name = "images/привет.py"
        content = self.file_system.get_file_content_text(old_name)
        self.file_system.rename_file(old_name, new_name)
        assert self.file_system.is_exist(new_name)
        assert content == self.file_system.get_file_content_text(new_name)

    def test_is_empty_not_existing_file(self):
        with pytest.raises(FileNotFoundError):
            self.file_system.file_is_empty("aaa.txt")

    def test_is_empty_file_on_directory(self):
        with pytest.raises(IsADirectoryError):
            self.file_system.file_is_empty("image")

    def test_is_empty_file_not_empty(self):
        assert not self.file_system.file_is_empty("hello.py")
        assert not self.file_system.file_is_empty("images/cars/6.jpg")

    def test_is_empty_file_empty(self):
        assert self.file_system.file_is_empty("images/future.png")
