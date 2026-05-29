# Contributing to OME-IRIS

Thanks for contributing to OME-IRIS.

This project is intentionally small: a lightweight bioimage dataset catalog with fetch/verify tooling. Keep changes simple, readable, and easy to validate.

## Development setup

1. Install dependencies:

```bash
uv sync
```

2. Run the test suite:

```bash
uv run --frozen pytest
```

3. Run pre-commit checks:

```bash
pre-commit run --all-files
```

4. (Optional) build docs:

```bash
uv sync --group docs
uv run --frozen sphinx-build docs/src docs/build
```

## Repository orientation

- Keep changes aligned with the project goal: a small, easy-to-use bioimage dataset catalog.
- Prefer working through the unified CLI and tests rather than relying on fixed internal paths.
- Treat schema, manifests, and validation tooling as evolving components.

## Common workflows

### Update or add a dataset

1. Add or edit a dataset manifest in the current manifest location.
1. Update the catalog metadata index used by the project.
1. Validate locally:

```bash
uv run ome-iris verify
uv run --frozen pytest
```

To generate a starter manifest + CSV row from a source path:

```bash
uv run ome-iris scaffold --source-path /path/to/dataset
uv run ome-iris scaffold --source-path /path/to/dataset --append-csv
uv run ome-iris scaffold --source-path /path/to/dataset --include-directory-entry --directory-path images --archive-format zip
```

### Use a custom data directory

```bash
uv run ome-iris fetch --data-dir /tmp/ome-iris-data
uv run ome-iris verify --data-dir /tmp/ome-iris-data
```

### Check fetch behavior

```bash
uv run ome-iris fetch --tier small
uv run ome-iris fetch --dataset <dataset-id>
uv run ome-iris export-rocrate --dataset <dataset-id>
```

If URLs are missing, fetch should report them clearly instead of failing silently.
Each fetched dataset directory includes `ro-crate-metadata.json` for provenance and relationship metadata.

For mixed-source datasets, add multiple `files` entries with per-file URLs. If a source is provided as an archive, you can use:

- `kind: directory`
- `archive_format: zip` or `archive_format: tar`
- required top-level `source_identifier` to define the local dataset root under `data/`
- `files[].path` relative to `data/<source_identifier>/`
- directory traversal is supported for GitHub `tree` URLs and local directories

`sha256` is optional, but recommended when URLs are stable.

You can also define top-level `relationships` entries to link components.
`from` and `to` must reference existing `files[].path` values.
Prefer standard relationship fields (`via_columns`, `filename_patterns`, `derived_from_columns`) before using `custom_metadata`.
Set `rocrate_predicate` on every relationship using an explicit absolute JSON-LD predicate URI (required).

## Custom metadata support

Custom metadata is first-class and validated.

- Use `custom_metadata` at manifest, source, or file level.
- `custom_metadata` must be an object/map.
- Supported value types: string, number, boolean, null, list, and nested objects.

If `custom_metadata` is not an object or contains unsupported types, `ome-iris verify` reports an error.

## Testing expectations

- Add or update tests for behavior changes.
- Prefer small, focused tests over broad integration tests.
- Keep the suite fast.

Recommended test loop:

```bash
uv run --frozen pytest -k fetch -q
uv run --frozen pytest -k verify -q
uv run --frozen pytest
```

## Pull request guidelines

- Keep PR scope tight and purpose-specific.
- Include a short summary of what changed and why.
- Include validation evidence (tests/checks run).
- Do not commit large data files.

## Style and design principles

- Prefer plain Python and minimal dependencies.
- Avoid adding workflow orchestration tools (DVC, Snakemake, Nextflow, Docker) for core functionality.
- Preserve the project goal: "a tiny data catalog with fetch and verify."
