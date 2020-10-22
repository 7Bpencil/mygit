from pathlib import Path


class Constants:
    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path
        self.mygit_ignore_path = self.workspace_path / ".mygit_ignore"
        self.mygit_path = self.workspace_path / ".mygit"
        self.mygit_log_path = self.mygit_path / "mygit.log"
        self.mygit_index_dir_path = self.mygit_path / "index"
        self.mygit_index_path = self.mygit_index_dir_path / "index"
        self.mygit_head_path = self.mygit_path / "head"
        self.mygit_objects_path = self.mygit_path / "objects"
        self.mygit_refs_path = self.mygit_path / "refs"
        self.mygit_branches_path = self.mygit_refs_path / "branches"
