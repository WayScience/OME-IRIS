from __future__ import annotations

import json
from pathlib import Path

from PIL import Image
import yaml

from OME_IRIS import datasets
from ome_iris import datasets as lower_datasets


def write_subset_manifest(path: Path, source_dir: Path) -> None:
    payload = {
        "id": "nf1-cellpainting-shrunken",
        "name": "NF1 Cell Painting shrunken",
        "description": "Example dataset",
        "tier": "small",
        "license": "CC-BY-4.0",
        "source_identifier": "NF1_cellpainting_data_shrunken",
        "source": {"repository": "https://example.org", "path": "data", "url": ""},
        "formats": ["tiff"],
        "files": [
            {
                "path": "images",
                "kind": "directory",
                "url": str(source_dir),
                "custom_metadata": {"role": "image_bundle"},
            }
        ],
    }
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")


def make_image(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("L", (4, 3), color=7).save(path)


def test_download_filters_images_by_channel_and_limit(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    make_image(source_dir / "A01_01_1_1_DAPI_001.tif")
    make_image(source_dir / "A01_01_2_1_GFP_001.tif")
    make_image(source_dir / "A02_01_1_1_DAPI_001.tif")

    manifests_dir = tmp_path / "datasets"
    manifests_dir.mkdir()
    write_subset_manifest(manifests_dir / "nf1.yaml", source_dir)

    result = datasets.download(
        "nf1",
        output_dir=tmp_path / "out",
        subset={"images": 1, "channels": ["DAPI"]},
        manifests_dir=manifests_dir,
    )

    assert result.downloaded == 1
    assert result.skipped == 0
    assert result.failed == []
    assert (tmp_path / "out" / "images" / "A01_01_1_1_DAPI_001.tif").exists()
    assert not (tmp_path / "out" / "images" / "A02_01_1_1_DAPI_001.tif").exists()

    manifest = json.loads((tmp_path / "out" / "manifest.json").read_text())
    assert manifest["dataset"]["id"] == "nf1-cellpainting-shrunken"
    assert manifest["subset"]["images"] == 1
    assert manifest["files"][0]["source_url"].endswith("A01_01_1_1_DAPI_001.tif")
    assert manifest["files"][0]["sha256"]
    assert manifest["files"][0]["shape"] == [3, 4]
    assert manifest["files"][0]["dtype"] == "uint8"


def test_lowercase_package_exposes_datasets_api() -> None:
    assert lower_datasets.download is datasets.download


def test_download_reuses_cached_files_and_validation_only_checks_manifest(
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "source"
    make_image(source_dir / "A01_01_1_1_DAPI_001.tif")
    manifests_dir = tmp_path / "datasets"
    manifests_dir.mkdir()
    write_subset_manifest(manifests_dir / "nf1.yaml", source_dir)

    first = datasets.download(
        "nf1",
        output_dir=tmp_path / "out",
        subset={"images": 1},
        manifests_dir=manifests_dir,
    )
    second = datasets.download(
        "nf1",
        output_dir=tmp_path / "out",
        subset={"images": 1},
        manifests_dir=manifests_dir,
    )
    validation = datasets.download(
        "nf1",
        output_dir=tmp_path / "out",
        validate_only=True,
        manifests_dir=manifests_dir,
    )

    assert first.downloaded == 1
    assert second.downloaded == 0
    assert second.skipped == 1
    assert validation.validated == 1
    assert validation.failed == []


def test_download_preset_expands_to_reproducible_subset_size(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    for index in range(3):
        make_image(source_dir / f"A0{index + 1}_01_1_1_DAPI_001.tif")
    manifests_dir = tmp_path / "datasets"
    manifests_dir.mkdir()
    write_subset_manifest(manifests_dir / "nf1.yaml", source_dir)

    result = datasets.download(
        "nf1",
        output_dir=tmp_path / "out",
        preset="tiny",
        manifests_dir=manifests_dir,
    )

    assert result.downloaded == 3
    assert result.manifest_path == tmp_path / "out" / "manifest.json"
