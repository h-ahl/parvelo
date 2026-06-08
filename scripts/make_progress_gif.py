"""Render the ``parallel_map`` progress bar to an animated gif.

Captures the real ``rich`` progress bar (same columns as ``parvelo.parallel``)
at each completion step, rasterises each frame via ``cairosvg``, and stitches
them into a gif with ``imageio``.

Run after syncing dev dependencies:

    uv sync --group dev
    uv run python scripts/make_progress_gif.py
"""

import io
from pathlib import Path

import cairosvg
import imageio.v2 as imageio
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
)

N_ITEMS = 24
CONSOLE_WIDTH = 64
SECONDS_PER_ITEM = 0.18  # virtual work time per item, drives the time-remaining estimate
OUTPUT = Path(__file__).resolve().parent.parent / "assets" / "parallel_map.gif"


def main() -> None:
    """Build the gif frame by frame and save it."""
    clock = {"t": 0.0}

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeRemainingColumn(),
        get_time=lambda: clock["t"],  # deterministic clock so frames are reproducible
        auto_refresh=False,
    )
    task = progress.add_task("Processing", total=N_ITEMS)

    frames = []
    for completed in range(N_ITEMS + 1):
        clock["t"] = completed * SECONDS_PER_ITEM
        progress.update(task, completed=completed)

        recorder = Console(record=True, width=CONSOLE_WIDTH, file=io.StringIO())
        recorder.print(progress.get_renderable())
        svg = recorder.export_svg(title="parallel_map")

        png_bytes = cairosvg.svg2png(bytestring=svg.encode())
        frames.append(imageio.imread(png_bytes))

    # Hold on the finished frame so the loop reads cleanly.
    frames.extend([frames[-1]] * 4)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    imageio.mimsave(OUTPUT, frames, duration=0.15, loop=0)
    print(f"wrote {OUTPUT} ({len(frames)} frames)")


if __name__ == "__main__":
    main()
