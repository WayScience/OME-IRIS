from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import re
from typing import Any
from urllib.request import urlopen

from PIL import Image
import yaml

from OME_IRIS.fetch import _download, _parse_github_tree_url


PRESET_SUBSETS: dict[str, dict[str, Any]] = {
    "tiny": {"images": 5},
    "small": {"images": 20},
    "benchmark": {"images": 100},
}

DATASET_ALIASES = {
    "nf1": "nf1-cellpainting-shrunken",
    "jump": "jump-plate-example",
}


@dataclass
class DownloadResult:
    downloaded: int = 0
    skipped: int = 0
    validated: int = 0
    failed: list[str] = field(default_factory=list)
    downloaded_items: list[str] = field(default_factory=list)
    skipped_items: list[str] = field(default_factory=list)
    validated_items: list[str] = field(default_factory=list)
    manifest_path: Path | None = None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _default_manifests_dir() -> Path:
    return Path(__file__).parent / "data" / "datasets"


def _load_manifests(manifests_dir: Path) -> list[dict[str, Any]]:
    return [
        yaml.safe_load(path.read_text(encoding="utf-8"))
        for path in sorted(manifests_dir.glob("*.yaml"))
    ]


def _resolve_dataset(dataset: str, manifests_dir: Path) -> dict[str, Any]:
    manifests = _load_manifests(manifests_dir)
    dataset_id = DATASET_ALIASES.get(dataset, dataset)
    exact = [manifest for manifest in manifests if manifest.get("id") == dataset_id]
    if exact:
        return exact[0]

    prefix = [
        manifest
        for manifest in manifests
        if str(manifest.get("id", "")).startswith(dataset)
    ]
    if len(prefix) == 1:
        return prefix[0]
    if not prefix:
        raise ValueError(f"Unknown dataset: {dataset}")
    matches = ", ".join(str(manifest.get("id")) for manifest in prefix)
    raise ValueError(f"Ambiguous dataset {dataset!r}; matched: {matches}")


def _merge_subset(preset: str | None, subset: dict[str, Any] | None) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    if preset:
        try:
            merged.update(PRESET_SUBSETS[preset])
        except KeyError as exc:
            choices = ", ".join(sorted(PRESET_SUBSETS))
            raise ValueError(
                f"Unknown preset {preset!r}; choose one of: {choices}"
            ) from exc
    if subset:
        merged.update(
            {key: value for key, value in subset.items() if value is not None}
        )
    return merged


def _github_tree_files(tree_url: str) -> list[tuple[str, str]]:
    parsed = _parse_github_tree_url(tree_url)
    if parsed is None:
        raise ValueError(f"Unsupported directory URL: {tree_url}")
    owner, repo, ref, subtree = parsed
    api_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{ref}?recursive=1"
    with urlopen(api_url) as response:  # nosec B310
        payload = json.loads(response.read().decode("utf-8"))

    prefix = f"{subtree.rstrip('/')}/"
    files: list[tuple[str, str]] = []
    for entry in payload.get("tree", []):
        blob_path = str(entry.get("path", ""))
        if entry.get("type") != "blob" or not blob_path.startswith(prefix):
            continue
        relative = blob_path[len(prefix) :]
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{blob_path}"
        files.append((relative, raw_url))
    return sorted(files)


def _directory_files(url: str) -> list[tuple[str, str]]:
    local_path = Path(url)
    if local_path.exists() and local_path.is_dir():
        files = []
        for source_file in local_path.rglob("*"):
            if source_file.is_file():
                files.append(
                    (str(source_file.relative_to(local_path)), str(source_file))
                )
        return sorted(files)
    return _github_tree_files(url)


def _filename_tokens(path: str) -> set[str]:
    return {
        token.casefold()
        for token in re.split(r"[^A-Za-z0-9]+", Path(path).name)
        if token
    }


def _matches_any_token(path: str, values: list[str] | tuple[str, ...] | None) -> bool:
    if not values:
        return True
    tokens = _filename_tokens(path)
    return any(value.casefold() in tokens for value in values)


def _matches_range(path: str, axis: str, value_range: tuple[int, int] | None) -> bool:
    if value_range is None:
        return True
    match = re.search(
        rf"(?:^|[^A-Za-z0-9]){axis}\D*0*(\d+)(?:[^A-Za-z0-9]|$)",
        path,
        re.IGNORECASE,
    )
    if match is None:
        return True
    value = int(match.group(1))
    start, stop = value_range
    return start <= value <= stop


def _matches_subset(path: str, subset: dict[str, Any]) -> bool:
    if not _matches_any_token(path, subset.get("channels")):
        return False
    for key in ("plate", "well", "site"):
        values = subset.get(key)
        if isinstance(values, str):
            values = [values]
        if not _matches_any_token(path, values):
            return False
    return (
        _matches_range(path, "z", subset.get("z"))
        and _matches_range(path, "t", subset.get("t"))
        and _matches_range(path, "c", subset.get("c"))
    )


def _select_files(
    file_rec: dict[str, Any], subset: dict[str, Any]
) -> list[dict[str, str]]:
    kind = file_rec.get("kind", "file")
    if kind != "directory":
        url = (file_rec.get("url") or "").strip()
        return (
            [{"relative_path": str(file_rec["path"]), "source_url": url}] if url else []
        )

    selected = []
    for relative, source_url in _directory_files(str(file_rec.get("url", ""))):
        if _matches_subset(relative, subset):
            selected.append(
                {
                    "relative_path": str(Path(str(file_rec["path"])) / relative),
                    "source_url": source_url,
                }
            )

    image_limit = subset.get("images")
    if image_limit is not None:
        selected = selected[: int(image_limit)]
    return selected


def _image_metadata(path: Path) -> tuple[list[int] | None, str | None]:
    try:
        with Image.open(path) as image:
            width, height = image.size
            bands = len(image.getbands())
            shape = [height, width] if bands == 1 else [height, width, bands]
            dtype_by_mode = {
                "1": "bool",
                "L": "uint8",
                "P": "uint8",
                "RGB": "uint8",
                "RGBA": "uint8",
                "I;16": "uint16",
                "I": "int32",
                "F": "float32",
            }
            return shape, dtype_by_mode.get(image.mode, image.mode)
    except Exception:  # noqa: BLE001
        return None, None


def _manifest_record(
    output_dir: Path,
    relative_path: str,
    source_url: str,
    file_rec: dict[str, Any],
) -> dict[str, Any]:
    target = output_dir / relative_path
    shape, dtype = _image_metadata(target)
    record: dict[str, Any] = {
        "path": relative_path,
        "source_url": source_url,
        "sha256": _sha256(target),
        "size_bytes": target.stat().st_size,
        "shape": shape,
        "dtype": dtype,
        "metadata": file_rec.get("custom_metadata", {}),
    }
    return record


def _write_subset_manifest(
    *,
    output_dir: Path,
    dataset_manifest: dict[str, Any],
    subset: dict[str, Any],
    files: list[dict[str, Any]],
) -> Path:
    manifest_path = output_dir / "manifest.json"
    payload = {
        "manifest_version": 1,
        "dataset": {
            "id": dataset_manifest.get("id"),
            "name": dataset_manifest.get("name"),
            "source_identifier": dataset_manifest.get("source_identifier"),
            "source": dataset_manifest.get("source", {}),
        },
        "subset": subset,
        "files": files,
    }
    manifest_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest_path


def _validate_existing_manifest(output_dir: Path) -> DownloadResult:
    manifest_path = output_dir / "manifest.json"
    result = DownloadResult(manifest_path=manifest_path)
    if not manifest_path.exists():
        result.failed.append(f"{manifest_path}: manifest not found")
        return result

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    for file_rec in payload.get("files", []):
        path = output_dir / file_rec["path"]
        if not path.exists():
            result.failed.append(f"{file_rec['path']}: missing file")
            continue
        actual = _sha256(path)
        if actual != file_rec.get("sha256"):
            result.failed.append(f"{file_rec['path']}: checksum mismatch")
            continue
        result.validated += 1
        result.validated_items.append(str(file_rec["path"]))
    return result


def download(
    dataset: str,
    output_dir: str | Path,
    subset: dict[str, Any] | None = None,
    *,
    preset: str | None = None,
    manifests_dir: str | Path | None = None,
    validate_only: bool = False,
    silent: bool = False,
) -> DownloadResult:
    """Download or validate a reproducible subset of a known dataset."""
    output_path = Path(output_dir)
    if validate_only:
        return _validate_existing_manifest(output_path)

    manifests_path = (
        Path(manifests_dir) if manifests_dir is not None else _default_manifests_dir()
    )
    dataset_manifest = _resolve_dataset(dataset, manifests_path)
    selected_subset = _merge_subset(preset, subset)
    output_path.mkdir(parents=True, exist_ok=True)

    result = DownloadResult(manifest_path=output_path / "manifest.json")
    manifest_files: list[dict[str, Any]] = []

    for file_rec in dataset_manifest.get("files", []):
        for selected in _select_files(file_rec, selected_subset):
            relative_path = selected["relative_path"]
            source_url = selected["source_url"]
            target = output_path / relative_path
            try:
                if target.exists():
                    result.skipped += 1
                    result.skipped_items.append(relative_path)
                else:
                    if not silent:
                        print(f"Downloading: {relative_path}")
                    _download(source_url, target, silent=silent)
                    result.downloaded += 1
                    result.downloaded_items.append(relative_path)
                manifest_files.append(
                    _manifest_record(output_path, relative_path, source_url, file_rec)
                )
            except Exception as exc:  # noqa: BLE001
                result.failed.append(f"{relative_path}: {exc}")

    result.manifest_path = _write_subset_manifest(
        output_dir=output_path,
        dataset_manifest=dataset_manifest,
        subset=selected_subset,
        files=manifest_files,
    )
    return result
