from __future__ import annotations

from OME_IRIS.cli import build_parser


def test_cli_has_download_fetch_verify_scaffold_and_export_rocrate_commands() -> None:
    parser = build_parser()
    help_text = parser.format_help()

    assert "download" in help_text
    assert "fetch" in help_text
    assert "verify" in help_text
    assert "scaffold" in help_text
    assert "export-rocrate" in help_text


def test_cli_download_accepts_subset_options() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "download",
            "nf1",
            "--output",
            ".benchmark-data/ome-iris/nf1",
            "--limit-images",
            "20",
            "--channel",
            "DAPI",
            "--validate-only",
        ]
    )

    assert args.command == "download"
    assert args.dataset == "nf1"
    assert args.output == ".benchmark-data/ome-iris/nf1"
    assert args.limit_images == 20
    assert args.channels == ["DAPI"]
    assert args.validate_only is True
