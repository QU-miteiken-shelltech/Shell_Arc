from pathlib import Path

class MSKFS_PathSolver:
    space_root = "msk"

    def __init__(self):
        self.root_dir = Path("/Users/shiinaayame/Documents/test_sa2027")

    def mskfs_path(self, *args) -> Path:
        return self.root_dir / "/".join(list(args))

    @property
    def mskfs_config(self) -> Path:
        space_root_dir = self.root_dir / MSKFS_PathSolver.space_root
        if not space_root_dir.exists():
            space_root_dir.mkdir(parents=True, exist_ok=False)
        return self.root_dir / MSKFS_PathSolver.space_root

    @property
    def mskfs_client(self) -> Path:
        client_root_dir = self.root_dir / "client"
        if not client_root_dir.exists():
            client_root_dir.mkdir(parents=True, exist_ok=False)
        return client_root_dir

    def mskfs_ref(self, ref: str) -> Path:
        return
    