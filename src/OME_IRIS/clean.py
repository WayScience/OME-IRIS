from __future__ import annotations

import shutil
from pathlib import Path


def clean_local_data(data_dir: Path) -> None:
    if data_dir.exists():
        shutil.rmtree(data_dir)
