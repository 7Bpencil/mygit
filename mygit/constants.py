class Constants:
    def __init__(self):
        self.mygit_ignore_path = ".mygit_ignore"
        self.mygit_path = ".mygit"
        self.mygit_index_dir_path = f"{self.mygit_path}/index"
        self.mygit_index_path = f"{self.mygit_index_dir_path}/index"
        self.mygit_head_path = f"{self.mygit_path}/head"
        self.mygit_objects_path = f"{self.mygit_path}/objects"
        self.mygit_refs_path = f"{self.mygit_path}/refs"
        self.mygit_branches_path = f"{self.mygit_refs_path}/branches"
