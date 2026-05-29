from __future__ import annotations

import json
import zipfile
from pathlib import Path

import yaml

from OME_IRIS.fetch import fetch_datasets


def write_manifest(path: Path, dataset_id: str, url: str = "") -> None:
    payload = {
        "id": dataset_id,
        "name": "Example",
        "description": "Example dataset",
        "tier": "small",
        "license": "CC-BY-4.0",
        "source_identifier": dataset_id,
        "source": {"repository": "https://example.org", "path": "data", "url": ""},
        "formats": ["csv"],
        "files": [
            {
                "path": "profiles.csv",
                "url": url,
                "sha256": "",
            }
        ],
    }
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")


def test_fetch_reports_missing_urls(tmp_path: Path) -> None:
    manifests_dir = tmp_path / "datasets"
    manifests_dir.mkdir()
    write_manifest(manifests_dir / "a.yaml", "a")

    result = fetch_datasets(manifests_dir=manifests_dir, data_dir=tmp_path / "data")

    assert result.downloaded == 0
    assert result.skipped == 0
    assert len(result.missing_urls) == 1
    assert "a/profiles.csv" in result.missing_urls[0]


def test_fetch_filters_by_dataset_id(tmp_path: Path) -> None:
    manifests_dir = tmp_path / "datasets"
    manifests_dir.mkdir()
    write_manifest(manifests_dir / "a.yaml", "a")
    write_manifest(manifests_dir / "b.yaml", "b")

    result = fetch_datasets(
        manifests_dir=manifests_dir,
        data_dir=tmp_path / "data",
        dataset_id="b",
    )

    assert len(result.missing_urls) == 1
    assert "b/profiles.csv" in result.missing_urls[0]


def test_fetch_skips_existing_file_when_checksum_not_provided(tmp_path: Path) -> None:
    manifests_dir = tmp_path / "datasets"
    manifests_dir.mkdir()
    write_manifest(manifests_dir / "a.yaml", "a", url="https://example.org/profiles.csv")

    existing = tmp_path / "data" / "a" / "profiles.csv"
    existing.parent.mkdir(parents=True)
    existing.write_text("already-here", encoding="utf-8")

    result = fetch_datasets(manifests_dir=manifests_dir, data_dir=tmp_path / "data")

    assert result.downloaded == 0
    assert result.skipped == 1
    assert result.failed == []


def test_fetch_downloads_directory_archive(tmp_path: Path) -> None:
    manifests_dir = tmp_path / "datasets"
    manifests_dir.mkdir()

    archive = tmp_path / "jump-images.zip"
    with zipfile.ZipFile(archive, "w") as zip_handle:
        zip_handle.writestr("A01.tiff", "fake-image-bytes")
        zip_handle.writestr("A02.tiff", "fake-image-bytes")

    payload = {
        "id": "jump-plate",
        "name": "Jump plate",
        "description": "Example dataset",
        "tier": "small",
        "license": "CC-BY-4.0",
        "source_identifier": "jump-plate",
        "source": {"repository": "https://example.org", "path": "data", "url": ""},
        "formats": ["tiff"],
        "files": [
            {
                "path": "images",
                "kind": "directory",
                "archive_format": "zip",
                "url": archive.as_uri(),
                "sha256": "",
            }
        ],
    }
    (manifests_dir / "jump.yaml").write_text(yaml.safe_dump(payload), encoding="utf-8")

    result = fetch_datasets(manifests_dir=manifests_dir, data_dir=tmp_path / "data")

    assert result.downloaded == 1
    assert (tmp_path / "data" / "jump-plate" / "images" / "A01.tiff").exists()


def test_fetch_traverses_local_directory_source(tmp_path: Path) -> None:
    manifests_dir = tmp_path / "datasets"
    manifests_dir.mkdir()

    source_dir = tmp_path / "source-images"
    (source_dir / "nested").mkdir(parents=True)
    (source_dir / "A01.tiff").write_text("fake-image", encoding="utf-8")
    (source_dir / "nested" / "A02.tiff").write_text("fake-image", encoding="utf-8")

    payload = {
        "id": "jump-plate",
        "name": "Jump plate",
        "description": "Example dataset",
        "tier": "small",
        "license": "CC-BY-4.0",
        "source_identifier": "jump-plate",
        "source": {"repository": "https://example.org", "path": "data", "url": ""},
        "formats": ["tiff"],
        "files": [
            {
                "path": "images",
                "kind": "directory",
                "url": str(source_dir),
            }
        ],
    }
    (manifests_dir / "jump.yaml").write_text(yaml.safe_dump(payload), encoding="utf-8")

    result = fetch_datasets(manifests_dir=manifests_dir, data_dir=tmp_path / "data")

    assert result.downloaded == 1
    assert (tmp_path / "data" / "jump-plate" / "images" / "A01.tiff").exists()
    assert (tmp_path / "data" / "jump-plate" / "images" / "nested" / "A02.tiff").exists()


def test_fetch_writes_dataset_rocrate_json(tmp_path: Path) -> None:
    manifests_dir = tmp_path / "datasets"
    manifests_dir.mkdir()
    write_manifest(manifests_dir / "a.yaml", "a")

    _ = fetch_datasets(manifests_dir=manifests_dir, data_dir=tmp_path / "data")

    rocrate_path = tmp_path / "data" / "a" / "ro-crate-metadata.json"
    assert rocrate_path.exists()
    payload = json.loads(rocrate_path.read_text(encoding="utf-8"))
    graph = payload["@graph"]
    root_dataset = next(node for node in graph if node.get("@id") == "./")
    assert root_dataset["identifier"] == "a"
