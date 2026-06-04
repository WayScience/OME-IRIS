# OME-IRIS

<img width="300" src="https://raw.githubusercontent.com/d33bs/OME-IRIS/main/docs/src/_static/ome-iris-logo.png?raw=true">

[![Build Status](https://github.com/d33bs/OME-IRIS/actions/workflows/run-tests.yml/badge.svg?branch=main)](https://github.com/d33bs/OME-IRIS/actions/workflows/run-tests.yml?query=branch%3Amain)
[![Publish Docs](https://github.com/d33bs/OME-IRIS/actions/workflows/publish-docs.yml/badge.svg?branch=main)](https://github.com/d33bs/OME-IRIS/actions/workflows/publish-docs.yml?query=branch%3Amain)
[![Publish PyPI](https://github.com/d33bs/OME-IRIS/actions/workflows/publish-pypi.yml/badge.svg)](https://github.com/d33bs/OME-IRIS/actions/workflows/publish-pypi.yml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![License](https://img.shields.io/github/license/d33bs/OME-IRIS)](https://github.com/d33bs/OME-IRIS/blob/main/LICENSE)
[![python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)

OME-IRIS is an open bioimage dataset catalog for benchmarking image input/output (IO), transformations, metadata management, and bioimage-linked workflows.

We also provide a small Python package by the same name (`ome_iris`) to help fetch and validate the datasets in the catalog.

Inspired by both the classic `iris.csv` dataset and the iris of the eye that brings images into focus, OME-IRIS aims to provide a collection of reference datasets for evaluating interoperable bioimage data formats, tools, and workflows.

## What this is

- A lightweight manifest catalog for small benchmark datasets
- A fetch + verify workflow with a single CLI
- LinkML-based schema definitions for dataset manifests

## What this is not

- Not a data portal
- Not DVC-based
- Not a large-file git storage approach
- Not a full ontology or end-to-end benchmark system yet

## Quick start

```bash
uv run ome-iris fetch --tier small
uv run ome-iris verify
uv run ome-iris export-rocrate --dataset nf1-cellpainting-shrunken
```

Download a reproducible subset for local development or benchmarking:

```bash
uv run ome-iris download nf1 \
  --output .benchmark-data/ome-iris/nf1 \
  --preset tiny \
  --channel DAPI
```

Python API:

```python
from ome_iris import datasets

datasets.download(
    "nf1",
    output_dir=".benchmark-data/ome-iris/nf1",
    subset={"images": 20, "channels": ["DAPI"]},
)
```

Fetch output modes:

```bash
uv run ome-iris fetch --tier small --verbose  # show per-file labels + downloader progress
uv run ome-iris fetch --tier small --silent   # suppress downloader progress output
```

## What `fetch` does

High-level flow when you run `ome-iris fetch`:

1. Loads dataset manifests from `--manifests-dir`.
1. Applies optional filters (`--dataset`, `--tier`).
1. Creates local dataset roots under `--data-dir/<source_identifier>/`.
1. Writes `ro-crate-metadata.json` into each dataset root.
1. Iterates over each `files` entry:
   - for `kind: file`: downloads the file URL (or skips if already present)
   - for `kind: directory`: traverses/downloads directory contents (or extracts archive sources)
1. Reports a summary:
   - downloaded count + item list
   - skipped count + item list
   - missing URLs
   - failed downloads

Output layout example:

```text
data/
  NF1_cellpainting_data_shrunken/
    ro-crate-metadata.json
    profiles.parquet
    images/
    masks/
```

Local files are stored under `./data/` by default.
Each dataset directory also gets `ro-crate-metadata.json` with source/provenance metadata from the manifest.

To use another data directory:

```bash
uv run ome-iris fetch --data-dir /tmp/ome-iris-data
uv run ome-iris verify --data-dir /tmp/ome-iris-data
```

## What `download` does

`ome-iris download` creates a small, reproducible subset under the exact `--output`
directory. It supports named dataset aliases such as `nf1`, preset sizes
(`tiny`, `small`, `benchmark`), image limits, channel filters, plate/well/site
filters, and Z/T/C ranges where filenames expose those values.

Downloaded subsets include `manifest.json` with the source dataset, selected
subset options, downloaded file paths, source URLs, SHA-256 checksums, file
sizes, image shapes, dtypes, and file metadata. Existing files are reused and
included in the manifest. Use `--validate-only` to verify an existing subset
cache against its manifest without downloading data:

```bash
uv run ome-iris download nf1 \
  --output .benchmark-data/ome-iris/nf1 \
  --validate-only
```

## Add a dataset

1. Add or update a dataset manifest and catalog metadata.
1. Include source, formats, and file-level metadata.
1. Run:

```bash
uv run ome-iris verify
```

Starter scaffolding command:

```bash
uv run ome-iris scaffold --source-path /path/to/JUMP_plate_BR00117006
uv run ome-iris scaffold --source-path /path/to/JUMP_plate_BR00117006 --append-csv
uv run ome-iris scaffold --source-path /path/to/JUMP_plate_BR00117006 --include-directory-entry --directory-path images --archive-format zip
```

The command guesses a dataset id/name/formats, writes a starter YAML manifest, and prints a suggested `datasets.csv` row.

### File entry patterns

- `source_identifier` is required at the top level of each manifest.
- All `files[].path` values are relative to `data/<source_identifier>/`.
- `sha256` is optional for file entries.
- Use `kind: directory` to fetch everything under a directory source.
  - For GitHub tree URLs (`https://github.com/<owner>/<repo>/tree/<ref>/<path>`), OME-IRIS traverses files under that subtree.
  - For local directory paths, OME-IRIS recursively copies files.
  - For archive URLs, set `archive_format` (`zip` or `tar`) to extract an archive into the destination directory.

### Relationships

Use an optional top-level `relationships` list to describe links between dataset components.

- `from`: source file path (must match a `files[].path`)
- `to`: target file path (must match a `files[].path`)
- `type`: relationship label (for example `links_to_images_by`, `links_to_masks_by`, `references_metadata`)
- `rocrate_predicate`: explicit RO-Crate/JSON-LD predicate URI for export (required)
- `via_columns` (optional): explicit table columns used for linking
- `filename_patterns` (optional): standardized filename templates used by the relationship
- `derived_from_columns` (optional): columns used when deriving one component from another (for example images -> masks)

Example:

```yaml
files:
  - path: profiles.parquet
  - path: images
    kind: directory

relationships:
  - from: profiles.parquet
    to: images
    type: links_to_images_by
    rocrate_predicate: http://schema.org/associatedMedia
```

Example directory entry:

```yaml
files:
  - path: jump-plate/images
    kind: directory
    archive_format: zip
    url: https://example.org/jump-plate-images.zip
    sha256: ""  # optional
```

## Custom metadata (first-class)

OME-IRIS supports custom metadata as a first-class field via `custom_metadata` objects at manifest, source, and file levels.

Rules:

- `custom_metadata` must be an object/map.
- Keys must be strings.
- Values may be strings, numbers, booleans, null, lists, or nested objects.

Example:

```yaml
id: jump-plate
source_identifier: JUMP_plate_BR00117006
name: JUMP plate BR00117006 (JUMP_plate_BR00117006) example
description: Plate-level cell painting benchmark subset.
tier: small
license: CC-BY-4.0
custom_metadata:
  study: jump-cp
  species: human
source:
  repository: https://example.org/repo
  path: datasets/JUMP_plate_BR00117006
  url: https://example.org/repo/tree/main/datasets/JUMP_plate_BR00117006
formats: [csv, tiff]
files:
  - path: profiles.csv
    url: https://example.org/files/profiles.csv
    sha256: "..."
    custom_metadata:
      role: profile_table
```

## Why large files are not committed

Large image/profile files make repositories slow and fragile for contributors and CI. OME-IRIS tracks metadata and download locations, while actual data is fetched locally when needed.

## Documentation

Build docs locally:

```bash
uv sync --group docs
uv run --frozen sphinx-build docs/src docs/build
```
