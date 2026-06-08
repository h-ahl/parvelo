"""Parallel ``map`` with an optional ``rich`` progress bar."""

import warnings
from collections.abc import Callable, Iterable, Iterator, Sized
from concurrent.futures import Executor, ProcessPoolExecutor, ThreadPoolExecutor
from enum import StrEnum
from multiprocessing import get_context
from typing import Any, Protocol, runtime_checkable

from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
)


@runtime_checkable
class ExecutorLike(Protocol):
    """Anything exposing a ``concurrent.futures``-style ``map``.

    Satisfied by ``concurrent.futures.Executor`` and any custom pool
    (e.g. a jax/ray wrapper) that maps ``func`` over ``items`` lazily and
    in input order, accepting a ``chunksize`` keyword.
    """

    def map(self, func: Callable[..., Any], /, *iterables: Iterable[Any], chunksize: int = 1) -> Iterator[Any]: ...


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
    executor: ExecutorLike | None = None,
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
        executor: Externally-owned pool to reuse across calls. When provided, ``backend``,
            ``n_workers``, and ``multiprocessing_context`` are ignored, and the executor is
            NOT shut down by ``parallel_map`` (the caller owns its lifecycle).

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

    # Branch 1: Custom executor provided
    if executor is not None:
        if verbose and (  # only warn if different from the defaults
            n_workers is not None
            or backend != Backend.PROCESS
            or multiprocessing_context != MultiprocessingContext.FORKSERVER
        ):
            warnings.warn(
                "An `executor` was provided; `backend`, `n_workers`, and `multiprocessing_context` are ignored.",
                stacklevel=2,
            )
        return collect(executor.map(func, items, chunksize=chunksize))

    # Branch 2: Serial execution due to n_workers=1
    if n_workers == 1:
        return collect(map(func, items))

    # Branch 3: Create a new executor
    executor: Executor = (
        ProcessPoolExecutor(max_workers=n_workers, mp_context=get_context(multiprocessing_context))
        if backend == Backend.PROCESS
        else ThreadPoolExecutor(max_workers=n_workers)
    )
    with executor:
        return collect(executor.map(func, items, chunksize=chunksize))
