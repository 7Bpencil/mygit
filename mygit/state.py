class State:
    def __init__(self):
        self.ignored_paths = set()
        self.current_indexed_paths = {}
        self.last_commit_indexed_path = {}

        self.status_is_checked = False
        self.status_indexed_paths = []
        self.status_indexed_but_changed_paths = []
        self.status_not_indexed_paths = []
