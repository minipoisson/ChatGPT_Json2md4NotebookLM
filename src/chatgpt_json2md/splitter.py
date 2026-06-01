"""Split Markdown blocks into numbered output files."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class OutputFile:
    path: Path
    content: str
    exceeds_limit: bool = False


def numbered_output_path(base: str | Path, index: int) -> Path:
    path = Path(base)
    suffix = path.suffix or ".md"
    stem_path = path.with_suffix("")
    return stem_path.with_name(f"{stem_path.name}-{index:02d}{suffix}")


def split_blocks(
    blocks: list[str],
    output_file: str | Path,
    limit: int,
    header: str,
) -> list[OutputFile]:
    if limit <= 0:
        raise ValueError("limit must be greater than zero")

    outputs: list[OutputFile] = []
    index = 1
    current = header
    current_bytes = _byte_len(current)

    for block in blocks:
        block_bytes = _byte_len(block)

        if current != header and current_bytes + block_bytes > limit:
            outputs.append(OutputFile(numbered_output_path(output_file, index), current))
            index += 1
            current = header
            current_bytes = _byte_len(current)

        current += block
        current_bytes += block_bytes

        if current == header + block and _byte_len(current) > limit:
            outputs.append(OutputFile(numbered_output_path(output_file, index), current, True))
            index += 1
            current = header
            current_bytes = _byte_len(current)

    if current != header or not outputs:
        outputs.append(OutputFile(numbered_output_path(output_file, index), current))

    return outputs


def ensure_writable_outputs(outputs: list[OutputFile], overwrite: bool) -> None:
    existing = [str(output.path) for output in outputs if output.path.exists()]
    if existing and not overwrite:
        joined = os.linesep.join(existing)
        raise FileExistsError(f"Output file already exists. Use --overwrite to replace it:{os.linesep}{joined}")


def write_outputs(outputs: list[OutputFile]) -> None:
    for output in outputs:
        output.path.parent.mkdir(parents=True, exist_ok=True)
        output.path.write_text(output.content, encoding="utf-8")


def _byte_len(text: str) -> int:
    return len(text.encode("utf-8"))

