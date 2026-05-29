from __future__ import annotations

from pathlib import Path
import shutil


def clean_local_data(data_dir: Path) -> None:
    if data_dir.exists():
        shutil.rmtree(data_dir)
