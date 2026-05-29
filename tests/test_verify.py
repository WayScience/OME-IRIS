from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

from OME_IRIS.verify import verify_datasets


def test_verify_detects_missing_file(tmp_path: Path) -> None:
    manifests_dir = tmp_path / "datasets"
    manifests_dir.mkdir()
    manifest = {
        "id": "demo",
        "name": "Demo",
        "description": "Demo",
        "tier": "tiny",
        "license": "CC0",
        "source_identifier": "demo",
        "source": {"repository": "x", "path": "y", "url": ""},
        "formats": ["csv"],
        "files": [{"path": "file.csv", "url": "", "sha256": ""}],
    }
    (manifests_dir / "demo.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")

    result = verify_datasets(manifests_dir=manifests_dir, data_dir=tmp_path / "data")

    assert result.ok is False
    assert any("missing" in issue.lower() for issue in result.issues)


def test_verify_validates_checksum(tmp_path: Path) -> None:
    manifests_dir = tmp_path / "datasets"
    manifests_dir.mkdir()
    data_dir = tmp_path / "data"
    target = data_dir / "demo" / "file.csv"
    target.parent.mkdir(parents=True)
    target.write_text("x,y\n1,2\n", encoding="utf-8")
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    manifest = {
        "id": "demo",
        "name": "Demo",
        "description": "Demo",
        "tier": "tiny",
        "license": "CC0",
        "source_identifier": "demo",
        "source": {"repository": "x", "path": "y", "url": ""},
        "formats": ["csv"],
        "files": [{"path": "file.csv", "url": "", "sha256": digest}],
    }
    (manifests_dir / "demo.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")

    result = verify_datasets(manifests_dir=manifests_dir, data_dir=data_dir)

    assert result.ok is True
    assert result.issues == []


def test_verify_accepts_custom_metadata_objects(tmp_path: Path) -> None:
    manifests_dir = tmp_path / "datasets"
    manifests_dir.mkdir()
    manifest = {
        "id": "demo",
        "name": "Demo",
        "description": "Demo",
        "tier": "tiny",
        "license": "CC0",
        "source_identifier": "demo",
        "custom_metadata": {"organism": "human", "channels": ["DNA", "RNA"]},
        "source": {
            "repository": "x",
            "path": "y",
            "url": "",
            "custom_metadata": {"accession": "ABC-123"},
        },
        "formats": ["csv"],
        "files": [
            {
                "path": "file.csv",
                "url": "",
                "sha256": "",
                "custom_metadata": {"modality": "profile"},
            }
        ],
    }
    (manifests_dir / "demo.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")

    result = verify_datasets(manifests_dir=manifests_dir, data_dir=tmp_path / "data")

    assert result.ok is False
    assert any("missing local file" in issue for issue in result.issues)
    assert not any(
        "custom_metadata must be an object" in issue for issue in result.issues
    )


def test_verify_rejects_invalid_custom_metadata_type(tmp_path: Path) -> None:
    manifests_dir = tmp_path / "datasets"
    manifests_dir.mkdir()
    manifest = {
        "id": "demo",
        "name": "Demo",
        "description": "Demo",
        "tier": "tiny",
        "license": "CC0",
        "source_identifier": "demo",
        "custom_metadata": ["not", "an", "object"],
        "source": {"repository": "x", "path": "y", "url": ""},
        "formats": ["csv"],
        "files": [{"path": "file.csv", "url": "", "sha256": ""}],
    }
    (manifests_dir / "demo.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")

    result = verify_datasets(manifests_dir=manifests_dir, data_dir=tmp_path / "data")

    assert result.ok is False
    assert any("custom_metadata must be an object" in issue for issue in result.issues)


def test_verify_directory_kind_checks_directory_content(tmp_path: Path) -> None:
    manifests_dir = tmp_path / "datasets"
    manifests_dir.mkdir()
    manifest = {
        "id": "demo",
        "name": "Demo",
        "description": "Demo",
        "tier": "tiny",
        "license": "CC0",
        "source_identifier": "demo",
        "source": {"repository": "x", "path": "y", "url": ""},
        "formats": ["tiff"],
        "files": [{"path": "images", "kind": "directory", "url": "", "sha256": ""}],
    }
    (manifests_dir / "demo.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")

    data_dir = tmp_path / "data"
    images_dir = data_dir / "demo" / "images"
    images_dir.mkdir(parents=True)
    (images_dir / "A01.tiff").write_text("fake", encoding="utf-8")

    result = verify_datasets(manifests_dir=manifests_dir, data_dir=data_dir)

    assert result.ok is True


def test_verify_accepts_valid_relationships(tmp_path: Path) -> None:
    manifests_dir = tmp_path / "datasets"
    manifests_dir.mkdir()
    manifest = {
        "id": "demo",
        "name": "Demo",
        "description": "Demo",
        "tier": "tiny",
        "license": "CC0",
        "source_identifier": "demo",
        "source": {"repository": "x", "path": "y", "url": ""},
        "formats": ["csv", "tiff"],
        "files": [
            {"path": "profiles.csv", "url": "", "sha256": ""},
            {"path": "images", "kind": "directory", "url": ""},
        ],
        "relationships": [
            {
                "from": "profiles.csv",
                "to": "images",
                "type": "links_to_images_by",
                "rocrate_predicate": "http://schema.org/associatedMedia",
            },
        ],
    }
    (manifests_dir / "demo.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")

    data_dir = tmp_path / "data"
    profiles = data_dir / "demo" / "profiles.csv"
    profiles.parent.mkdir(parents=True)
    profiles.write_text("x,y\n1,2\n", encoding="utf-8")
    images_dir = data_dir / "demo" / "images"
    images_dir.mkdir(parents=True)
    (images_dir / "A01.tiff").write_text("fake", encoding="utf-8")

    result = verify_datasets(manifests_dir=manifests_dir, data_dir=data_dir)

    assert result.ok is True


def test_verify_rejects_relationship_with_unknown_path(tmp_path: Path) -> None:
    manifests_dir = tmp_path / "datasets"
    manifests_dir.mkdir()
    manifest = {
        "id": "demo",
        "name": "Demo",
        "description": "Demo",
        "tier": "tiny",
        "license": "CC0",
        "source_identifier": "demo",
        "source": {"repository": "x", "path": "y", "url": ""},
        "formats": ["csv"],
        "files": [{"path": "profiles.csv", "url": "", "sha256": ""}],
        "relationships": [
            {
                "from": "profiles.csv",
                "to": "images",
                "type": "links_to_images_by",
                "rocrate_predicate": "http://schema.org/associatedMedia",
            },
        ],
    }
    (manifests_dir / "demo.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")

    result = verify_datasets(manifests_dir=manifests_dir, data_dir=tmp_path / "data")

    assert result.ok is False
    assert any("unknown 'to' path" in issue for issue in result.issues)


def test_verify_rejects_relationship_missing_rocrate_predicate(tmp_path: Path) -> None:
    manifests_dir = tmp_path / "datasets"
    manifests_dir.mkdir()
    manifest = {
        "id": "demo",
        "name": "Demo",
        "description": "Demo",
        "tier": "tiny",
        "license": "CC0",
        "source_identifier": "demo",
        "source": {"repository": "x", "path": "y", "url": ""},
        "formats": ["csv", "tiff"],
        "files": [
            {"path": "profiles.csv", "url": "", "sha256": ""},
            {"path": "images", "kind": "directory", "url": ""},
        ],
        "relationships": [
            {"from": "profiles.csv", "to": "images", "type": "links_to_images_by"},
        ],
    }
    (manifests_dir / "demo.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")

    result = verify_datasets(manifests_dir=manifests_dir, data_dir=tmp_path / "data")

    assert result.ok is False
    assert any(
        "missing required 'rocrate_predicate'" in issue for issue in result.issues
    )


def test_verify_rejects_relationship_non_uri_rocrate_predicate(tmp_path: Path) -> None:
    manifests_dir = tmp_path / "datasets"
    manifests_dir.mkdir()
    manifest = {
        "id": "demo",
        "name": "Demo",
        "description": "Demo",
        "tier": "tiny",
        "license": "CC0",
        "source_identifier": "demo",
        "source": {"repository": "x", "path": "y", "url": ""},
        "formats": ["csv", "tiff"],
        "files": [
            {"path": "profiles.csv", "url": "", "sha256": ""},
            {"path": "images", "kind": "directory", "url": ""},
        ],
        "relationships": [
            {
                "from": "profiles.csv",
                "to": "images",
                "type": "links_to_images_by",
                "rocrate_predicate": "prov:wasDerivedFrom",
            },
        ],
    }
    (manifests_dir / "demo.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")

    result = verify_datasets(manifests_dir=manifests_dir, data_dir=tmp_path / "data")

    assert result.ok is False
    assert any(
        "rocrate_predicate must be an absolute URI" in issue for issue in result.issues
    )
