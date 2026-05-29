from __future__ import annotations

import json
from pathlib import Path

import yaml

from OME_IRIS.rocrate import export_rocrate_metadata


def test_export_rocrate_metadata_writes_file(tmp_path: Path) -> None:
    manifests_dir = tmp_path / "datasets"
    manifests_dir.mkdir()

    manifest = {
        "id": "demo",
        "name": "Demo",
        "description": "Demo dataset",
        "tier": "tiny",
        "license": "CC0",
        "source_identifier": "demo_source",
        "source": {"repository": "x", "path": "y", "url": ""},
        "formats": ["csv"],
        "files": [
            {"path": "profiles.csv", "url": "https://example.org/profiles.csv"},
            {"path": "images", "kind": "directory", "url": "https://example.org/images"},
        ],
        "relationships": [
            {
                "from": "profiles.csv",
                "to": "images",
                "type": "links_to_images_by",
                "rocrate_predicate": "http://schema.org/associatedMedia",
            }
        ],
    }
    (manifests_dir / "demo.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")

    out = export_rocrate_metadata(
        manifests_dir=manifests_dir,
        dataset_id="demo",
        data_dir=tmp_path / "data",
    )

    assert out.exists()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert "@graph" in payload
    assert any(node.get("@id") == "profiles.csv" for node in payload["@graph"])
