"""Tests for :func:`parvelo.parallel_map`."""

from collections.abc import Iterator

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
