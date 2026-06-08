# parvelo

A tiny utility for parallel `map` with a `rich` progress bar.

`parvelo.parallel_map` runs a function over an iterable using either a process
pool (CPU-bound work) or a thread pool (I/O-bound work), preserves input order,
and optionally renders a progress bar.

![parallel_map progress bar](assets/parallel_map.gif)

## Install

Requires Python 3.13.

```bash
pip install parvelo
```

From source:

```bash
git clone https://github.com/h-ahl/parvelo.git
cd parvelo
uv sync --extra lint --group dev
```

## Usage

```python
import time

from parvelo import Backend, parallel_map


def square(x: int) -> int:
    return x * x


def fetch(url: str) -> str:
    time.sleep(0.05)  # stand-in for network I/O
    return url


# CPU-bound work across processes (default)
results = parallel_map(square, range(10))

# I/O-bound work across threads
urls = [f"https://example.com/{i}" for i in range(16)]
results = parallel_map(fetch, urls, backend=Backend.THREAD, n_workers=16)

# Run serially (handy for debugging), skipping executor overhead
results = parallel_map(square, range(10), n_workers=1)
```

### Reusing or injecting your own executor

Pass an `executor` to reuse a caller-owned pool across calls instead of creating one
each time. Any object with a `concurrent.futures`-style `map(func, *iterables, chunksize=1)`
qualifies (matched by the `ExecutorLike` protocol), so a stdlib executor or a custom
wrapper around a ray/jax pool both work. When `executor` is provided, `backend`,
`n_workers`, and `multiprocessing_context` are ignored, and parvelo does not shut the
executor down (you own its lifecycle).

```python
from concurrent.futures import ProcessPoolExecutor

from parvelo import parallel_map


def square(x: int) -> int:
    return x * x


with ProcessPoolExecutor() as pool:
    a = parallel_map(square, range(10), executor=pool)
    b = parallel_map(square, range(10, 20), executor=pool)  # pool reused, not recreated
```

## Development

```bash
just setup       # create the environment
just test        # run the test suite
just lint        # ruff check
just format      # ruff format
just typecheck   # ty check
just pre-commit  # run all pre-commit hooks
```
