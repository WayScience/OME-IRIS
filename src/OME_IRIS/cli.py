from __future__ import annotations

import argparse
from pathlib import Path

from OME_IRIS.clean import clean_local_data
from OME_IRIS.datasets import download
from OME_IRIS.fetch import fetch_datasets
from OME_IRIS.rocrate import export_rocrate_metadata
from OME_IRIS.scaffold import scaffold_dataset_manifest
from OME_IRIS.verify import verify_datasets


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ome-iris", description="Fetch and verify OME-IRIS datasets"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    download_cmd = sub.add_parser(
        "download", help="Download a reproducible dataset subset"
    )
    download_cmd.add_argument("dataset")
    download_cmd.add_argument("--output", required=True)
    download_cmd.add_argument("--preset", choices=["tiny", "small", "benchmark"])
    download_cmd.add_argument("--limit-images", type=int)
    download_cmd.add_argument("--channel", dest="channels", action="append")
    download_cmd.add_argument("--plate", action="append")
    download_cmd.add_argument("--well", action="append")
    download_cmd.add_argument("--site", action="append")
    download_cmd.add_argument("--z-range", nargs=2, type=int, metavar=("START", "STOP"))
    download_cmd.add_argument("--t-range", nargs=2, type=int, metavar=("START", "STOP"))
    download_cmd.add_argument("--c-range", nargs=2, type=int, metavar=("START", "STOP"))
    download_cmd.add_argument("--validate-only", action="store_true")
    download_cmd.add_argument("--manifests-dir", default="src/OME_IRIS/data/datasets")
    download_cmd.add_argument("--silent", action="store_true")

    fetch_cmd = sub.add_parser("fetch", help="Fetch dataset files")
    fetch_cmd.add_argument("--dataset", dest="dataset_id")
    fetch_cmd.add_argument("--tier", choices=["tiny", "small", "realistic"])
    fetch_cmd.add_argument("--manifests-dir", default="src/OME_IRIS/data/datasets")
    fetch_cmd.add_argument("--data-dir", default="data")
    fetch_mode = fetch_cmd.add_mutually_exclusive_group()
    fetch_mode.add_argument("--verbose", action="store_true")
    fetch_mode.add_argument("--silent", action="store_true")

    verify_cmd = sub.add_parser("verify", help="Verify local datasets")
    verify_cmd.add_argument("--manifests-dir", default="src/OME_IRIS/data/datasets")
    verify_cmd.add_argument("--data-dir", default="data")

    clean_cmd = sub.add_parser("clean", help="Remove local fetched data")
    clean_cmd.add_argument("--data-dir", default="data")

    scaffold_cmd = sub.add_parser(
        "scaffold",
        help="Generate starter dataset manifest and CSV row from a source path",
    )
    scaffold_cmd.add_argument("--source-path", required=True)
    scaffold_cmd.add_argument("--dataset-id")
    scaffold_cmd.add_argument("--name", dest="dataset_name")
    scaffold_cmd.add_argument(
        "--tier", choices=["tiny", "small", "realistic"], default="small"
    )
    scaffold_cmd.add_argument("--license", dest="license_name", default="TBD")
    scaffold_cmd.add_argument("--source-repository", default="")
    scaffold_cmd.add_argument("--source-url", default="")
    scaffold_cmd.add_argument("--include-directory-entry", action="store_true")
    scaffold_cmd.add_argument("--directory-path", default="images")
    scaffold_cmd.add_argument("--archive-format", choices=["zip", "tar"], default="zip")
    scaffold_cmd.add_argument("--manifests-dir", default="src/OME_IRIS/data/datasets")
    scaffold_cmd.add_argument("--catalog-csv", default="src/OME_IRIS/data/datasets.csv")
    scaffold_cmd.add_argument("--append-csv", action="store_true")
    scaffold_cmd.add_argument("--force", action="store_true")

    rocrate_cmd = sub.add_parser(
        "export-rocrate",
        help="Export RO-Crate metadata for a dataset into the fetched dataset directory",
    )
    rocrate_cmd.add_argument("--dataset", dest="dataset_id", required=True)
    rocrate_cmd.add_argument("--manifests-dir", default="src/OME_IRIS/data/datasets")
    rocrate_cmd.add_argument("--data-dir", default="data")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "download":
        subset = {
            "images": args.limit_images,
            "channels": args.channels,
            "plate": args.plate,
            "well": args.well,
            "site": args.site,
            "z": tuple(args.z_range) if args.z_range else None,
            "t": tuple(args.t_range) if args.t_range else None,
            "c": tuple(args.c_range) if args.c_range else None,
        }
        result = download(
            args.dataset,
            output_dir=Path(args.output),
            subset=subset,
            preset=args.preset,
            manifests_dir=Path(args.manifests_dir),
            validate_only=args.validate_only,
            silent=args.silent,
        )
        print(f"Downloaded: {result.downloaded}")
        print(f"Skipped: {result.skipped}")
        print(f"Validated: {result.validated}")
        if result.manifest_path:
            print(f"Manifest: {result.manifest_path}")
        if result.failed:
            print("Failed:")
            for item in result.failed:
                print(f"- {item}")
            return 1
        return 0

    if args.command == "fetch":
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
    if args.command == "clean":
        clean_local_data(Path(args.data_dir))
        print(f"Removed local data directory: {args.data_dir}")
        return 0
    if args.command == "scaffold":
        result = scaffold_dataset_manifest(
            source_path=args.source_path,
            manifests_dir=Path(args.manifests_dir),
            dataset_id=args.dataset_id,
            dataset_name=args.dataset_name,
            tier=args.tier,
            license_name=args.license_name,
            source_repository=args.source_repository,
            source_url=args.source_url,
            include_directory_entry=args.include_directory_entry,
            directory_path=args.directory_path,
            archive_format=args.archive_format,
            append_csv=args.append_csv,
            catalog_csv=Path(args.catalog_csv),
            force=args.force,
        )
        print(f"Manifest created: {result.manifest_path}")
        print("Suggested datasets.csv row:")
        print(result.csv_row)
        if args.append_csv:
            print(f"Appended row to: {args.catalog_csv}")
        return 0
    if args.command == "export-rocrate":
        out_path = export_rocrate_metadata(
            manifests_dir=Path(args.manifests_dir),
            dataset_id=args.dataset_id,
            data_dir=Path(args.data_dir),
        )
        print(f"RO-Crate metadata written: {out_path}")
        return 0

    result = verify_datasets(
        manifests_dir=Path(args.manifests_dir),
        data_dir=Path(args.data_dir),
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
