from pathlib import Path

class MSKFS_PathSolver:
    space_root = "msk"

    def __init__(self):
        self.root_dir = Path("/Users/shiinaayame/Documents/test_sa2027")

    def mskfs_path(self, *args) -> Path:
        return self.root_dir / "/".join(list(args))

    @property
    def mskfs_config(self) -> Path:
        return self.root_dir / MSKFS_PathSolver.space_root

    def mskfs_ref(self, ref: str) -> Path:
        return
    