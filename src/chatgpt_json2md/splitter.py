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
    header_bytes = _byte_len(header)
    current = header
    current_bytes = header_bytes
    just_reset = True

    for block in blocks:
        block_bytes = _byte_len(block)

        if not just_reset and current_bytes + block_bytes > limit:
            outputs.append(OutputFile(numbered_output_path(output_file, index), current))
            index += 1
            current = header
            current_bytes = header_bytes
            just_reset = True

        current += block
        current_bytes += block_bytes

        if just_reset and current_bytes > limit:
            outputs.append(OutputFile(numbered_output_path(output_file, index), current, True))
            index += 1
            current = header
            current_bytes = header_bytes
        else:
            just_reset = False

    if not just_reset or not outputs:
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

