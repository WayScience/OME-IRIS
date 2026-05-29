from __future__ import annotations

from pathlib import Path

import yaml

from OME_IRIS.scaffold import scaffold_dataset_manifest


def test_scaffold_creates_manifest_and_guesses_fields(tmp_path: Path) -> None:
    source = tmp_path / "JUMP_plate_BR00117006"
    source.mkdir()
    (source / "cells.csv").write_text("a,b\n1,2\n", encoding="utf-8")

    manifests_dir = tmp_path / "manifests"
    result = scaffold_dataset_manifest(source_path=str(source), manifests_dir=manifests_dir)

    assert result.dataset_id == "jump-plate-br00117006"
    assert result.manifest_path.exists()

    data = yaml.safe_load(result.manifest_path.read_text(encoding="utf-8"))
    assert data["name"] == "Jump Plate Br00117006 example"
    assert data["formats"] == ["csv"]
    assert data["source_identifier"] == "JUMP_plate_BR00117006"
    assert data["files"][0]["path"] == "profiles.csv"
    assert "sha256" not in data["files"][0]
    assert data["files"][0]["custom_metadata"]["role"] == "profile_table"


def test_scaffold_appends_catalog_row(tmp_path: Path) -> None:
    source = tmp_path / "nf1_cellpainting"
    source.mkdir()
    (source / "profiles.parquet").write_text("dummy", encoding="utf-8")

    csv_path = tmp_path / "datasets.csv"
    result = scaffold_dataset_manifest(
        source_path=str(source),
        manifests_dir=tmp_path / "manifests",
        append_csv=True,
        catalog_csv=csv_path,
    )

    content = csv_path.read_text(encoding="utf-8")
    assert content.startswith("id,name,tier,formats,benchmark_roles,license,source")
    assert result.dataset_id in content
    assert "parquet" in content


def test_scaffold_can_include_directory_entry(tmp_path: Path) -> None:
    source = tmp_path / "plate"
    source.mkdir()
    (source / "profiles.parquet").write_text("dummy", encoding="utf-8")

    result = scaffold_dataset_manifest(
        source_path=str(source),
        manifests_dir=tmp_path / "manifests",
        include_directory_entry=True,
        directory_path="images",
        archive_format="tar",
    )

    data = yaml.safe_load(result.manifest_path.read_text(encoding="utf-8"))
    directory_entries = [item for item in data["files"] if item.get("kind") == "directory"]
    assert len(directory_entries) == 1
    assert directory_entries[0]["path"] == "images"
    assert directory_entries[0]["archive_format"] == "tar"
