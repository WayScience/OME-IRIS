from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
from pathlib import Path

import yaml


@dataclass
class VerifyResult:
    ok: bool
    issues: list[str]


REQUIRED_FIELDS = {
    "id",
    "name",
    "description",
    "tier",
    "license",
    "source_identifier",
    "source",
    "formats",
    "files",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_manifests(manifests_dir: Path) -> list[tuple[Path, dict]]:
    return [
        (path, yaml.safe_load(path.read_text(encoding="utf-8")))
        for path in sorted(manifests_dir.glob("*.yaml"))
    ]


def _check_openable(path: Path) -> None:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        path.read_text(encoding="utf-8")
    elif suffix == ".parquet":
        import pandas as pd

        try:
            pd.read_parquet(path)
        except ImportError:
            # Optional parquet engines (pyarrow/fastparquet) may be unavailable
            # in lightweight environments; existence/checksum validation still applies.
            return
    elif suffix in {".tif", ".tiff", ".png", ".jpg", ".jpeg"}:
        from PIL import Image

        with Image.open(path) as _img:
            pass


def _is_valid_metadata_value(value: object) -> bool:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return True
    if isinstance(value, list):
        return all(_is_valid_metadata_value(item) for item in value)
    if isinstance(value, dict):
        return all(
            isinstance(key, str) and _is_valid_metadata_value(item)
            for key, item in value.items()
        )
    return False


def _validate_custom_metadata(payload: dict, owner: str, issues: list[str]) -> None:
    if "custom_metadata" not in payload:
        return
    custom_metadata = payload["custom_metadata"]
    if not isinstance(custom_metadata, dict):
        issues.append(f"{owner}: custom_metadata must be an object")
        return
    if not _is_valid_metadata_value(custom_metadata):
        issues.append(f"{owner}: custom_metadata contains unsupported value types")


def _validate_relationships(
    manifest: dict, manifest_name: str, issues: list[str]
) -> None:
    relationships = manifest.get("relationships")
    if relationships is None:
        return
    if not isinstance(relationships, list):
        issues.append(f"{manifest_name}: relationships must be a list")
        return

    file_paths: set[str] = set()
    for file_rec in manifest.get("files", []):
        if isinstance(file_rec, dict) and isinstance(file_rec.get("path"), str):
            file_paths.add(file_rec["path"])

    for idx, rel in enumerate(relationships):
        owner = f"{manifest_name}:relationships[{idx}]"
        if not isinstance(rel, dict):
            issues.append(f"{owner}: relationship must be an object")
            continue
        source = rel.get("from")
        target = rel.get("to")
        rel_type = rel.get("type")
        if not isinstance(source, str) or not source.strip():
            issues.append(f"{owner}: missing required 'from'")
            continue
        if not isinstance(target, str) or not target.strip():
            issues.append(f"{owner}: missing required 'to'")
            continue
        if not isinstance(rel_type, str) or not rel_type.strip():
            issues.append(f"{owner}: missing required 'type'")
            continue
        rocrate_predicate = rel.get("rocrate_predicate")
        if not isinstance(rocrate_predicate, str) or not rocrate_predicate.strip():
            issues.append(f"{owner}: missing required 'rocrate_predicate'")
            continue
        if not rocrate_predicate.startswith(("http://", "https://")):
            issues.append(f"{owner}: rocrate_predicate must be an absolute URI")
            continue
        if source not in file_paths:
            issues.append(f"{owner}: unknown 'from' path: {source}")
        if target not in file_paths:
            issues.append(f"{owner}: unknown 'to' path: {target}")


def verify_datasets(manifests_dir: Path, data_dir: Path) -> VerifyResult:
    issues: list[str] = []
    for manifest_path, manifest in _load_manifests(manifests_dir):
        missing = REQUIRED_FIELDS.difference(manifest.keys())
        if missing:
            issues.append(
                f"{manifest_path.name}: missing required fields: {sorted(missing)}"
            )
            continue
        source_identifier = str(manifest.get("source_identifier", "")).strip()
        if not source_identifier:
            issues.append(
                f"{manifest_path.name}: source_identifier must be a non-empty string"
            )
            continue

        _validate_custom_metadata(manifest, manifest_path.name, issues)
        _validate_relationships(manifest, manifest_path.name, issues)
        source = manifest.get("source", {})
        if isinstance(source, dict):
            _validate_custom_metadata(source, f"{manifest_path.name}:source", issues)

        for file_rec in manifest.get("files", []):
            if isinstance(file_rec, dict):
                _validate_custom_metadata(
                    file_rec, f"{manifest_path.name}:file", issues
                )
            kind = file_rec.get("kind", "file")
            rel_path = file_rec.get("path")
            if not rel_path:
                issues.append(f"{manifest_path.name}: file record missing path")
                continue
            target = data_dir / source_identifier / rel_path
            reported_path = f"{source_identifier}/{rel_path}"
            if kind == "directory":
                if (
                    not target.exists()
                    or not target.is_dir()
                    or not any(target.iterdir())
                ):
                    issues.append(f"{reported_path}: missing local directory content")
                continue

            if not target.exists():
                issues.append(f"{reported_path}: missing local file")
                continue
            expected = (file_rec.get("sha256") or "").strip()
            if expected and _sha256(target) != expected:
                issues.append(f"{reported_path}: checksum mismatch")
                continue
            try:
                _check_openable(target)
            except Exception as exc:  # noqa: BLE001
                issues.append(f"{reported_path}: failed to open ({exc})")

    return VerifyResult(ok=not issues, issues=issues)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify OME-IRIS datasets")
    parser.add_argument("--manifests-dir", default="src/OME_IRIS/data/datasets")
    parser.add_argument("--data-dir", default="data")
    args = parser.parse_args()

    result = verify_datasets(
        manifests_dir=Path(args.manifests_dir), data_dir=Path(args.data_dir)
    )
    if result.ok:
        print("Verification passed")
        return 0
    print("Verification failed")
    for issue in result.issues:
        print(f"- {issue}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
