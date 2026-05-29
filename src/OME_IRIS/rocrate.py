from __future__ import annotations

import json
from pathlib import Path

import yaml


def _load_manifest(manifests_dir: Path, dataset_id: str) -> dict:
    for path in sorted(manifests_dir.glob("*.yaml")):
        manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
        if manifest.get("id") == dataset_id:
            manifest["_manifest_path"] = str(path)
            return manifest
    raise FileNotFoundError(f"Dataset manifest not found for id: {dataset_id}")


def _build_rocrate_payload(manifest: dict) -> dict:
    root_id = "./"
    graph: list[dict] = [
        {
            "@id": "ro-crate-metadata.json",
            "@type": "CreativeWork",
            "about": {"@id": root_id},
            "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
        },
        {
            "@id": root_id,
            "@type": "Dataset",
            "name": manifest.get("name", manifest.get("id", "dataset")),
            "description": manifest.get("description", ""),
            "license": manifest.get("license", ""),
            "identifier": manifest.get("source_identifier", ""),
            "hasPart": [{"@id": rec["path"]} for rec in manifest.get("files", [])],
        },
    ]

    file_nodes: dict[str, dict] = {}
    for rec in manifest.get("files", []):
        path = rec["path"]
        node: dict = {
            "@id": path,
            "@type": "Dataset" if rec.get("kind") == "directory" else "File",
            "name": Path(path).name,
        }
        if rec.get("url"):
            node["contentUrl"] = rec["url"]
        file_nodes[path] = node

    for rel in manifest.get("relationships", []):
        src = rel["from"]
        dst = rel["to"]
        src_node = file_nodes.get(src)
        if src_node is None:
            continue
        predicate = rel["rocrate_predicate"]
        src_node.setdefault(predicate, [])
        src_node[predicate].append({"@id": dst})

    graph.extend(file_nodes.values())

    return {
        "@context": [
            "https://w3id.org/ro/crate/1.1/context",
            {"prov": "http://www.w3.org/ns/prov#"},
        ],
        "@graph": graph,
    }


def write_rocrate_metadata(manifest: dict, data_dir: Path) -> Path:
    source_identifier = manifest["source_identifier"]
    dataset_dir = data_dir / source_identifier
    dataset_dir.mkdir(parents=True, exist_ok=True)
    rocrate_payload = _build_rocrate_payload(manifest)
    out_path = dataset_dir / "ro-crate-metadata.json"
    out_path.write_text(json.dumps(rocrate_payload, indent=2), encoding="utf-8")
    return out_path


def export_rocrate_metadata(
    manifests_dir: Path, dataset_id: str, data_dir: Path
) -> Path:
    manifest = _load_manifest(manifests_dir, dataset_id)
    return write_rocrate_metadata(manifest, data_dir)
