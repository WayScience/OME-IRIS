"""OME-IRIS package."""

__all__ = ["__version__"]

try:
    from ._version import version as __version__
except ImportError:  # pragma: no cover
    __version__ = "0+unknown"
