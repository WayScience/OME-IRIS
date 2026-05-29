from __future__ import annotations

from OME_IRIS.cli import build_parser


def test_cli_has_fetch_verify_scaffold_and_export_rocrate_commands() -> None:
    parser = build_parser()
    help_text = parser.format_help()

    assert "fetch" in help_text
    assert "verify" in help_text
    assert "scaffold" in help_text
    assert "export-rocrate" in help_text
