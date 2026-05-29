# Examples

## Fetch all `small` tier datasets

```bash
uv run ome-iris fetch --tier small
```

## Verify local data

```bash
uv run ome-iris verify
```

## Use a custom local data directory

```bash
uv run ome-iris fetch --data-dir /tmp/ome-iris-data
uv run ome-iris verify --data-dir /tmp/ome-iris-data
```

## Scaffold a new dataset manifest from an external source path

```bash
uv run ome-iris scaffold --source-path /path/to/JUMP_plate_BR00117006
```

## Scaffold and append a starter CSV row

```bash
uv run ome-iris scaffold --source-path /path/to/JUMP_plate_BR00117006 --append-csv
```
