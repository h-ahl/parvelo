"""Parallel ``map`` with an optional ``rich`` progress bar."""

from collections.abc import Callable, Iterable, Sized
from concurrent.futures import Executor, ProcessPoolExecutor, ThreadPoolExecutor
from enum import StrEnum
from multiprocessing import get_context

from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
)


class Backend(StrEnum):
    """Backend for parallel processing."""

    PROCESS = "process"  # separate processes, best for CPU-bound work (sidesteps the GIL)
    THREAD = "thread"  # shared-memory threads, best for I/O-bound work


class MultiprocessingContext(StrEnum):
    """Start method for the process backend."""

    FORKSERVER = "forkserver"  # fork from a clean server process; safe default with threads
    FORK = "fork"  # clone the parent; fast but unsafe alongside threads
    SPAWN = "spawn"  # fresh interpreter; safest but slowest to start


def parallel_map[T, R](
    func: Callable[[T], R],
    items: Iterable[T],
    *,
    backend: Backend = Backend.PROCESS,
    n_workers: int | None = None,
    chunksize: int = 1,
    description: str = "Processing",
    total: int | None = None,
    verbose: bool = True,
    multiprocessing_context: MultiprocessingContext = MultiprocessingContext.FORKSERVER,
) -> list[R]:
    """Map ``func`` over ``items`` in parallel, preserving input order.

    Args:
        func: Function applied to each item.
        items: Items to process.
        backend: ``"process"`` for CPU-bound work, ``"thread"`` for I/O-bound work.
        n_workers: Worker count; ``None`` uses the executor default. ``1`` runs serially, skipping executor overhead.
        chunksize: Number of items dispatched per task (process backend benefits most).
        description: Label shown next to the progress bar.
        total: Item count for the progress bar when ``items`` has no ``len()``.
        verbose: Show a rich progress bar.
        multiprocessing_context: Start method for the process backend; ignored for threads.

    Returns:
        Results in the same order as ``items``.
    """
    if total is None and isinstance(items, Sized):
        total = len(items)

    def collect(results: Iterable[R]) -> list[R]:
        """Collect results from the executor."""
        if not verbose:
            return list(results)
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeRemainingColumn(),
        ) as bar:
            return list(bar.track(results, total=total, description=description))

    if n_workers == 1:
        return collect(map(func, items))

    executor: Executor = (
        ProcessPoolExecutor(max_workers=n_workers, mp_context=get_context(multiprocessing_context))
        if backend == Backend.PROCESS
        else ThreadPoolExecutor(max_workers=n_workers)
    )
    with executor:
        return collect(executor.map(func, items, chunksize=chunksize))
