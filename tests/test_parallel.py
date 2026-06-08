"""Tests for :func:`parvelo.parallel_map`."""

from collections.abc import Callable, Iterable, Iterator
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import Any

import pytest

from parvelo import Backend, parallel_map


def square(x: int) -> int:
    """Square a number (module-level so it is picklable for the process backend)."""
    return x * x


def gen(n: int) -> Iterator[int]:
    """Yield ``0..n-1`` as a non-``Sized`` iterable."""
    yield from range(n)


@pytest.mark.parametrize("backend", [Backend.PROCESS, Backend.THREAD])
def test_preserves_order(backend: Backend) -> None:
    items = list(range(20))
    assert parallel_map(square, items, backend=backend, verbose=False) == [square(i) for i in items]


def test_serial_path() -> None:
    items = list(range(10))
    assert parallel_map(square, items, n_workers=1, verbose=False) == [square(i) for i in items]


def test_thread_backend_with_workers() -> None:
    items = list(range(50))
    result = parallel_map(square, items, backend=Backend.THREAD, n_workers=4, verbose=False)
    assert result == [square(i) for i in items]


def test_verbose_progress_bar() -> None:
    items = list(range(5))
    assert parallel_map(square, items, verbose=True) == [square(i) for i in items]


def test_non_sized_iterable_with_total() -> None:
    result = parallel_map(square, gen(8), total=8, n_workers=1, verbose=True)
    assert result == [square(i) for i in range(8)]


def test_empty_input() -> None:
    assert parallel_map(square, [], verbose=False) == []


def test_injected_process_executor_not_shut_down() -> None:
    items = list(range(20))
    with ProcessPoolExecutor(max_workers=2) as pool:
        assert parallel_map(square, items, executor=pool, verbose=False) == [square(i) for i in items]
        # Pool should still be usable afterwards (parallel_map must not shut it down).
        assert list(pool.map(square, items)) == [square(i) for i in items]


def test_injected_thread_executor() -> None:
    items = list(range(50))
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert parallel_map(square, items, executor=pool, verbose=False) == [square(i) for i in items]


def test_injected_executor_reused_across_calls() -> None:
    with ThreadPoolExecutor(max_workers=4) as pool:
        first = parallel_map(square, range(10), executor=pool, verbose=False)
        second = parallel_map(square, range(10, 20), executor=pool, verbose=False)
    assert first == [square(i) for i in range(10)]
    assert second == [square(i) for i in range(10, 20)]


class _MapOnlyExecutor:
    """Minimal duck-typed executor exposing only a ``map`` method."""

    def map(self, func: Callable[..., Any], /, *iterables: Iterable[Any], chunksize: int = 1) -> Iterator[Any]:  # noqa: ARG002
        return map(func, *iterables)


def test_injected_duck_typed_executor() -> None:
    items = list(range(10))
    result = parallel_map(square, items, executor=_MapOnlyExecutor(), verbose=False)
    assert result == [square(i) for i in items]


def test_injected_executor_overrides_serial_n_workers() -> None:
    items = list(range(10))
    with ThreadPoolExecutor(max_workers=2) as pool:
        result = parallel_map(square, items, executor=pool, n_workers=1, verbose=False)
    assert result == [square(i) for i in items]


def test_injected_executor_warns_on_conflicting_n_workers() -> None:
    items = list(range(5))
    with ThreadPoolExecutor(max_workers=2) as pool, pytest.warns(UserWarning, match="executor"):
        result = parallel_map(square, items, executor=pool, n_workers=4, verbose=True)
    assert result == [square(i) for i in items]
