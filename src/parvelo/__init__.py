"""parvelo: parallel ``map`` with an optional progress bar."""

from parvelo.parallel import Backend, MultiprocessingContext, parallel_map

__version__ = "0.2.0"

__all__ = ["Backend", "MultiprocessingContext", "parallel_map"]
