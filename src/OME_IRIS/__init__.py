"""OME-IRIS package."""

from __future__ import annotations

import sys

from . import datasets

__all__ = ["__version__", "datasets"]

try:
    from ._version import version as __version__
except ImportError:  # pragma: no cover
    __version__ = "0+unknown"

sys.modules.setdefault("ome_iris", sys.modules[__name__])
sys.modules.setdefault("ome_iris.datasets", datasets)
