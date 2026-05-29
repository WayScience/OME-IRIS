from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import yaml


KNOWN_FORMATS = {
    ".csv": "csv",
    ".parquet": "parquet",
    ".tif": "tiff",
    ".tiff": "tiff",
    ".png": "png",
    ".jpg": "jpeg",
    ".jpeg": "jpeg",
}


@dataclass
class ScaffoldResult:
    dataset_id: str
    manifest_path: Path
    csv_row: str


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "dataset"


def _guess_dataset_id(source_path: str) -> str:
    name = Path(source_path).name or source_path
    return _slugify(name)


def _guess_dataset_name(source_path: str) -> str:
    name = Path(source_path).name or source_path
    text = re.sub(r"[_-]+", " ", name).strip()
    if not text:
        return "Dataset"
    return text.title()


def _guess_formats(source_path: str) -> list[str]:
    root = Path(source_path)
    if not root.exists() or not root.is_dir():
        return ["csv"]

    found: set[str] = set()
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix in KNOWN_FORMATS:
            found.add(KNOWN_FORMATS[suffix])
    return sorted(found) if found else ["csv"]


def scaffold_dataset_manifest(
    source_path: str,
    manifests_dir: Path,
    dataset_id: str | None = None,
    dataset_name: str | None = None,
    tier: str = "small",
    license_name: str = "TBD",
    source_repository: str = "",
    source_url: str = "",
    include_directory_entry: bool = False,
    directory_path: str = "images",
    archive_format: str = "zip",
    append_csv: bool = False,
    catalog_csv: Path | None = None,
    force: bool = False,
) -> ScaffoldResult:
    manifests_dir.mkdir(parents=True, exist_ok=True)
    final_id = dataset_id or _guess_dataset_id(source_path)
    final_name = dataset_name or f"{_guess_dataset_name(source_path)} example"
    formats = _guess_formats(source_path)

    manifest_path = manifests_dir / f"{final_id}.yaml"
    if manifest_path.exists() and not force:
        raise FileExistsError(f"Manifest already exists: {manifest_path}")

    primary_ext = formats[0]
    primary_file = "profiles.parquet" if primary_ext == "parquet" else "profiles.csv"
    payload = {
        "id": final_id,
        "name": final_name,
        "description": "TODO: describe this dataset and benchmark role.",
        "tier": tier,
        "license": license_name,
        "source_identifier": Path(source_path).name or final_id,
        "source": {
            "repository": source_repository,
            "path": source_path,
            "url": source_url,
        },
        "formats": formats,
        "files": [
            {
                "path": primary_file,
                "url": "",
                "custom_metadata": {"role": "profile_table"},
            }
        ],
    }
    if include_directory_entry:
        payload["files"].append(
            {
                "path": directory_path,
                "kind": "directory",
                "archive_format": archive_format,
                "url": "",
                "custom_metadata": {"role": "image_bundle"},
            }
        )

    manifest_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    row = (
        f'{final_id},"{final_name}",{tier},"{",".join(formats)}",'
        f'TODO,"{license_name}","{source_repository or "TBD"}"'
    )

    if append_csv and catalog_csv is not None:
        catalog_csv.parent.mkdir(parents=True, exist_ok=True)
        if not catalog_csv.exists():
            catalog_csv.write_text(
                "id,name,tier,formats,benchmark_roles,license,source\n",
                encoding="utf-8",
            )
        with catalog_csv.open("a", encoding="utf-8") as handle:
            handle.write(f"{row}\n")

    return ScaffoldResult(dataset_id=final_id, manifest_path=manifest_path, csv_row=row)
