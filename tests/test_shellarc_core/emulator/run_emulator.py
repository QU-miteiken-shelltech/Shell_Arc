import argparse
import asyncio
import json
import sys
import tempfile
from pathlib import Path

from emu_app import run_app
from emu_backend import ShellArcEmulatorBackend

DEFAULT_PROJ_SETTINGS = {
    "cut_num": 5,
    "components": {
        "bg": {"format": "png"},
        "character": {"format": "png"},
        "effect": {"format": "png"},
        "compo": {"format": "mp4"},
    },
}


def load_proj_settings(path: str | None) -> dict:
    if path:
        settings_path = Path(path)
        if settings_path.exists():
            return json.loads(settings_path.read_text(encoding="utf-8"))
        print(f"指定されたproj_settingsファイルが見つかりません: {path}")
        print("組み込みのデフォルト設定を使用します")
    return DEFAULT_PROJ_SETTINGS


def main() -> int:
    parser = argparse.ArgumentParser(description="ShellArc Discord Emulator")
    parser.add_argument(
        "--proj-settings",
        default=None,
        help="project_settings.json 相当のファイルパス(省略時は組み込みのデフォルトを使用)",
    )
    args = parser.parse_args()
    proj_settings = load_proj_settings(args.proj_settings)

    git_repo_dir = Path(tempfile.mkdtemp(prefix="shellarc_emu_git_"))
    print("疑似Gitリポジトリを作成します(このプロセスからは削除しません):")
    print(f"  {git_repo_dir}")
    print(f"使用する proj_settings: {json.dumps(proj_settings, ensure_ascii=False)}")

    # 参照スクリプトの make_proj_repo() 関数と同じ手順で初期化する
    backend = asyncio.run(
        ShellArcEmulatorBackend.create(git_repo_dir=git_repo_dir, proj_settings=proj_settings)
    )
    print("疑似リポジトリの初期化が完了しました (project_main.json / stage/cutN を作成済み)")

    return run_app(backend=backend, git_repo_dir=git_repo_dir)


if __name__ == "__main__":
    sys.exit(main())