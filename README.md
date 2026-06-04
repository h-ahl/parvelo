# parvelo

A tiny utility for parallel `map` with a `rich` progress bar.

`parvelo.parallel_map` runs a function over an iterable using either a process
pool (CPU-bound work) or a thread pool (I/O-bound work), preserves input order,
and optionally renders a progress bar.

## Install

```bash
uv sync --extra lint --group dev
```

## Usage

```python
from parvelo import Backend, parallel_map


def square(x: int) -> int:
    return x * x


# CPU-bound work across processes (default)
results = parallel_map(square, range(10))

# I/O-bound work across threads
results = parallel_map(fetch, urls, backend=Backend.THREAD, n_workers=16)

# Run serially (handy for debugging), skipping executor overhead
results = parallel_map(square, range(10), n_workers=1)
```

## Development

```bash
just setup       # create the environment
just test        # run the test suite
just lint        # ruff check
just format      # ruff format
just pre-commit  # run all pre-commit hooks
```
