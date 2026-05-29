from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
from urllib.parse import urlparse
from urllib.request import urlopen, urlretrieve
import zipfile

from OME_IRIS.rocrate import write_rocrate_metadata
import yaml


@dataclass
class FetchResult:
    downloaded: int
    skipped: int
    missing_urls: list[str]
    failed: list[str] = field(default_factory=list)
    downloaded_items: list[str] = field(default_factory=list)
    skipped_items: list[str] = field(default_factory=list)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_manifests(manifests_dir: Path) -> list[dict]:
    return [
        yaml.safe_load(path.read_text(encoding="utf-8"))
        for path in sorted(manifests_dir.glob("*.yaml"))
    ]


def _select_downloader() -> str | None:
    for candidate in ("aria2c", "curl", "wget"):
        if shutil.which(candidate):
            return candidate
    return None


def _download(url: str, target: Path, silent: bool = False) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    parsed = urlparse(url)

    # Handle local file URIs/paths without external download tools.
    if parsed.scheme == "file":
        source_path = Path(parsed.path)
        shutil.copy2(source_path, target)
        return
    if parsed.scheme == "":
        local_path = Path(url)
        if local_path.exists() and local_path.is_file():
            shutil.copy2(local_path, target)
            return

    downloader = _select_downloader()
    if downloader == "aria2c":
        cmd = ["aria2c", "-o", target.name, "-d", str(target.parent), url]
        if silent:
            cmd.insert(1, "--summary-interval=0")
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL if silent else None)
        return
    if downloader == "curl":
        cmd = ["curl", "-L", "-o", str(target), url]
        if silent:
            cmd = ["curl", "-sS", "-L", "-o", str(target), url]
        subprocess.run(cmd, check=True)
        return
    if downloader == "wget":
        cmd = ["wget", "-O", str(target), url]
        if silent:
            cmd = ["wget", "-q", "-O", str(target), url]
        subprocess.run(cmd, check=True)
        return
    urlretrieve(url, str(target))  # nosec B310


def _extract_archive(
    archive_path: Path, target_dir: Path, archive_format: str | None = None
) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    fmt = archive_format
    if fmt is None:
        suffixes = "".join(archive_path.suffixes).lower()
        if suffixes.endswith(".zip"):
            fmt = "zip"
        elif (
            suffixes.endswith(".tar.gz")
            or suffixes.endswith(".tgz")
            or suffixes.endswith(".tar")
        ):
            fmt = "tar"
        else:
            raise ValueError(f"Unable to infer archive format for {archive_path.name}")

    if fmt == "zip":
        with zipfile.ZipFile(archive_path) as zip_handle:
            zip_handle.extractall(target_dir)
        return
    if fmt == "tar":
        with tarfile.open(archive_path) as tar_handle:
            tar_handle.extractall(target_dir)
        return
    raise ValueError(f"Unsupported archive_format: {fmt}")


def _download_directory_local(source_dir: Path, target_dir: Path) -> int:
    count = 0
    target_dir.mkdir(parents=True, exist_ok=True)
    for source_file in source_dir.rglob("*"):
        if not source_file.is_file():
            continue
        relative = source_file.relative_to(source_dir)
        destination = target_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, destination)
        count += 1
    return count


def _parse_github_tree_url(url: str) -> tuple[str, str, str, str] | None:
    parsed = urlparse(url)
    if parsed.netloc not in {"github.com", "www.github.com"}:
        return None
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 5 or parts[2] != "tree":
        return None
    owner, repo, _tree, ref = parts[:4]
    subtree = "/".join(parts[4:])
    return owner, repo, ref, subtree


def _download_directory_github_tree(
    tree_url: str, target_dir: Path, silent: bool = False
) -> int:
    parsed = _parse_github_tree_url(tree_url)
    if parsed is None:
        raise ValueError(f"Unsupported directory URL: {tree_url}")
    owner, repo, ref, subtree = parsed
    api_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{ref}?recursive=1"
    with urlopen(api_url) as response:  # nosec B310
        payload = json.loads(response.read().decode("utf-8"))
    tree_entries = payload.get("tree", [])
    prefix = f"{subtree.rstrip('/')}/"
    matching_blobs = [
        entry
        for entry in tree_entries
        if entry.get("type") == "blob" and str(entry.get("path", "")).startswith(prefix)
    ]
    if not matching_blobs:
        raise ValueError(f"No files found under GitHub tree path: {subtree}")

    target_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for entry in matching_blobs:
        blob_path = str(entry["path"])
        relative = blob_path[len(prefix) :]
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{blob_path}"
        destination = target_dir / relative
        _download(raw_url, destination, silent=silent)
        count += 1
    return count


def _download_directory(url: str, target_dir: Path, silent: bool = False) -> int:
    # Local directory path support for quick internal demos/scaffolding.
    local_path = Path(url)
    if local_path.exists() and local_path.is_dir():
        return _download_directory_local(local_path, target_dir)
    return _download_directory_github_tree(url, target_dir, silent=silent)


def fetch_datasets(
    manifests_dir: Path,
    data_dir: Path,
    dataset_id: str | None = None,
    tier: str | None = None,
    verbose: bool = False,
    silent: bool = False,
) -> FetchResult:
    manifests = _load_manifests(manifests_dir)
    if dataset_id:
        manifests = [m for m in manifests if m.get("id") == dataset_id]
    if tier:
        manifests = [m for m in manifests if m.get("tier") == tier]

    downloaded = 0
    skipped = 0
    missing_urls: list[str] = []
    failed: list[str] = []
    downloaded_items: list[str] = []
    skipped_items: list[str] = []

    for manifest in manifests:
        source_identifier = str(manifest.get("source_identifier", "")).strip()
        if not source_identifier:
            failed.append(f"{manifest.get('id', 'unknown')}: missing source_identifier")
            continue
        dataset_dir = data_dir / source_identifier
        write_rocrate_metadata(manifest, data_dir)
        for file_rec in manifest.get("files", []):
            kind = file_rec.get("kind", "file")
            rel_path = file_rec["path"]
            target = dataset_dir / rel_path
            reported_path = f"{source_identifier}/{rel_path}"
            expected = file_rec.get("sha256", "")
            url = (file_rec.get("url") or "").strip()
            if not url:
                missing_urls.append(reported_path)
                continue
            try:
                if verbose or not silent:
                    print(f"Downloading: {reported_path}")
                    print(f"  from: {url}")
                if kind == "directory":
                    if target.exists() and any(target.iterdir()):
                        skipped += 1
                        skipped_items.append(reported_path)
                        continue
                    if file_rec.get("archive_format") or url.lower().endswith(
                        (".zip", ".tar", ".tar.gz", ".tgz")
                    ):
                        with tempfile.TemporaryDirectory() as temp_dir:
                            archive_name = Path(url).name or "archive"
                            archive_path = Path(temp_dir) / archive_name
                            _download(url, archive_path, silent=silent)
                            if expected and _sha256(archive_path) != expected:
                                raise ValueError("archive checksum mismatch")
                            _extract_archive(
                                archive_path,
                                target,
                                archive_format=file_rec.get("archive_format"),
                            )
                    else:
                        _download_directory(url, target, silent=silent)
                    downloaded += 1
                    downloaded_items.append(reported_path)
                    continue

                if target.exists():
                    if expected:
                        if _sha256(target) == expected:
                            skipped += 1
                            skipped_items.append(reported_path)
                            continue
                    else:
                        skipped += 1
                        skipped_items.append(reported_path)
                        continue
                _download(url, target, silent=silent)
                downloaded += 1
                downloaded_items.append(reported_path)
            except Exception as exc:  # noqa: BLE001
                failed.append(f"{reported_path}: {exc}")

    return FetchResult(
        downloaded=downloaded,
        skipped=skipped,
        missing_urls=missing_urls,
        failed=failed,
        downloaded_items=downloaded_items,
        skipped_items=skipped_items,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch OME-IRIS datasets")
    parser.add_argument("--dataset", dest="dataset_id")
    parser.add_argument("--tier", choices=["tiny", "small", "realistic"])
    parser.add_argument("--manifests-dir", default="src/OME_IRIS/data/datasets")
    parser.add_argument("--data-dir", default="data")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--verbose", action="store_true")
    mode.add_argument("--silent", action="store_true")
    args = parser.parse_args()

    result = fetch_datasets(
        manifests_dir=Path(args.manifests_dir),
        data_dir=Path(args.data_dir),
        dataset_id=args.dataset_id,
        tier=args.tier,
        verbose=args.verbose,
        silent=args.silent,
    )
    print(f"Downloaded: {result.downloaded}")
    print(f"Skipped: {result.skipped}")
    if result.downloaded_items:
        print("Downloaded items:")
        for item in result.downloaded_items:
            print(f"- {item}")
    if result.skipped_items:
        print("Skipped items:")
        for item in result.skipped_items:
            print(f"- {item}")
    if result.missing_urls:
        print("Missing URLs:")
        for item in result.missing_urls:
            print(f"- {item}")
    if result.failed:
        print("Failed downloads:")
        for item in result.failed:
            print(f"- {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
