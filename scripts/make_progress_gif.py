"""Render the ``parallel_map`` progress bar to an animated gif.

Captures the real ``rich`` progress bar (same columns as ``parvelo.parallel``)
at each completion step, rasterises Rich segments with Pillow so the bar matches
terminal output, then stitches frames into a gif with ``imageio``.

Run after syncing dev dependencies:

    uv sync --group dev
    uv run python scripts/make_progress_gif.py
"""

from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.segment import Segment
from rich.style import Style

N_ITEMS = 24
CONSOLE_WIDTH = 64
SECONDS_PER_ITEM = 0.18  # virtual work time per item, drives the time-remaining estimate
FONT_SIZE = 14
PADDING = (8, 6)
BACKGROUND = (30, 30, 30)
OUTPUT = Path(__file__).resolve().parent.parent / "assets" / "parallel_map.gif"

_MONO_FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/noto/NotoSansMono-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
)


def _mono_font_path() -> str:
    for path in _MONO_FONT_CANDIDATES:
        if Path(path).is_file():
            return path
    msg = "No monospace font found; install Noto Sans Mono or DejaVu Sans Mono."
    raise FileNotFoundError(msg)


def _style_rgb(style: Style | None) -> tuple[int, int, int]:
    if style is None or style.color is None or style.color.is_default:
        return (212, 212, 212)
    triplet = style.color.get_truecolor()
    return (triplet.red, triplet.green, triplet.blue)


def _render_frame(console: Console, renderable: object, font: ImageFont.FreeTypeFont, width: int) -> Image.Image:
    """Rasterise a Rich renderable the same way a terminal would draw it."""
    options = console.options.update_width(width)
    segments = console.render(renderable, options)
    lines = [
        line
        for line in Segment.split_and_crop_lines(segments, width)
        if any(segment.text and segment.text != "\n" for segment in line)
    ]

    cell_width = font.getlength("M")
    cell_height = FONT_SIZE + 6
    image = Image.new(
        "RGB",
        (int(PADDING[0] * 2 + cell_width * width), int(PADDING[1] * 2 + cell_height * len(lines))),
        BACKGROUND,
    )
    draw = ImageDraw.Draw(image)

    y = PADDING[1]
    for line in lines:
        x = PADDING[0]
        for segment in line:
            if not segment.text or segment.text == "\n":
                continue
            rgb = _style_rgb(segment.style)
            for char in segment.text:
                draw.text((x, y), char, font=font, fill=rgb)
                x += font.getlength(char)
        y += cell_height

    return image


def main() -> None:
    """Build the gif frame by frame and save it."""
    clock = {"t": 0.0}
    console = Console(width=CONSOLE_WIDTH, color_system="truecolor")
    font = ImageFont.truetype(_mono_font_path(), FONT_SIZE)

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

    frames: list[np.ndarray] = []
    for completed in range(N_ITEMS + 1):
        clock["t"] = completed * SECONDS_PER_ITEM
        progress.update(task, completed=completed)
        frame = _render_frame(console, progress.get_renderable(), font, CONSOLE_WIDTH)
        frames.append(np.asarray(frame))

    # Hold on the finished frame so the loop reads cleanly.
    frames.extend([frames[-1]] * 4)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    imageio.mimsave(OUTPUT, frames, duration=0.15, loop=0)
    print(f"wrote {OUTPUT} ({len(frames)} frames)")


if __name__ == "__main__":
    main()
