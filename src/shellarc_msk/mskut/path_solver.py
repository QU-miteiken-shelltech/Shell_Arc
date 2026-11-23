from pathlib import Path

class MSKUT_PathSolver:
    space_root = "msk"

    def __init__(self):
        self.root_dir = Path("/Users/shiinaayame/Documents/test_sa2027")

    def mskfs_path(self, *args) -> Path:
        return self.root_dir / "/".join(list(args))

    @property
    def mskfs_space(self) -> Path:
        space_root_dir = self.root_dir / MSKUT_PathSolver.space_root
        if not space_root_dir.exists():
            space_root_dir.mkdir(parents=True, exist_ok=False)
        return self.root_dir / MSKUT_PathSolver.space_root

    @property
    def mskfs_client(self) -> Path:
        client_root_dir = self.root_dir / "client"
        if not client_root_dir.exists():
            client_root_dir.mkdir(parents=True, exist_ok=False)
        return client_root_dir

    @property
    def mskfs_tmp(self) -> Path:
        tmp_root_dir = self.root_dir / "tmp"
        if not tmp_root_dir.exists():
            tmp_root_dir.mkdir(parents=True, exist_ok=False)
        return tmp_root_dir

    @property
    def mskfs_backup(self) -> Path:
        backup_root_dir = self.root_dir / "backup"
        if not backup_root_dir.exists():
            backup_root_dir.mkdir(parents=True, exist_ok=False)
        return backup_root_dir

    def mskfs_ref(self, ref: str) -> Path:
        return
    