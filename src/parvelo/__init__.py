"""parvelo: parallel ``map`` with an optional progress bar."""

from parvelo.parallel import Backend, ExecutorLike, MultiprocessingContext, parallel_map

__version__ = "0.3.1"

__all__ = ["Backend", "ExecutorLike", "MultiprocessingContext", "parallel_map"]
