"""Command line interface for ChatGPT Json2md for NotebookLM."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

_CONVERSATIONS_GLOB = "conversations*.json"

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from chatgpt_json2md.converter import convert_conversations
    from chatgpt_json2md.markdown import render_header
    from chatgpt_json2md.splitter import ensure_writable_outputs, split_blocks, write_outputs
else:
    from .converter import convert_conversations
    from .markdown import render_header
    from .splitter import ensure_writable_outputs, split_blocks, write_outputs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert ChatGPT conversations.json to Markdown for NotebookLM"
    )
    parser.add_argument(
        "--input",
        "--input_file",
        dest="input_file",
        nargs="+",
        default=["conversations.json"],
        help="Path(s), directory, or glob pattern for ChatGPT conversations JSON files",
    )
    parser.add_argument("--output_file", default="ChatGPT_History.md", help="Base output Markdown filename")
    parser.add_argument("--limit", type=int, default=1_000_000, help="Max bytes per output file")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing numbered output files")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    input_paths = resolve_input_files(args.input_file)
    if not input_paths:
        print(f"Error: input file not found: {', '.join(args.input_file)}", file=sys.stderr)
        return 1

    try:
        data = load_conversations(input_paths)
    except json.JSONDecodeError as exc:
        print(f"JSON decode error: {exc}", file=sys.stderr)
        return 1
    except (OSError, TypeError, ValueError) as exc:
        print(f"Error reading input file: {exc}", file=sys.stderr)
        return 1

    try:
        converted = convert_conversations(data)
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        outputs = split_blocks(
            converted.blocks,
            args.output_file,
            args.limit,
            render_header(generated_at),
        )
        ensure_writable_outputs(outputs, args.overwrite)
        write_outputs(outputs)
    except (FileExistsError, ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    for warning in converted.warnings:
        print(f"Warning: {warning}", file=sys.stderr)
    for output in outputs:
        note = " (exceeds limit)" if output.exceeds_limit else ""
        print(f"Written: {output.path}{note}")
    print(f"Done: {len(converted.blocks)} conversations / {len(outputs)} files")
    return 0


def resolve_input_files(inputs: Sequence[str]) -> list[Path]:
    paths: list[Path] = []
    for raw in inputs:
        candidate = Path(raw)
        if candidate.is_dir():
            paths.extend(sorted(candidate.glob(_CONVERSATIONS_GLOB)))
        elif _has_glob(raw):
            paths.extend(sorted(candidate.parent.glob(candidate.name)))
        elif candidate.exists():
            paths.append(candidate)

    seen: set[Path] = set()
    unique_paths: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved not in seen and path.is_file():
            seen.add(resolved)
            unique_paths.append(path)
    return unique_paths


def load_conversations(paths: Sequence[Path]) -> list[dict]:
    conversations: list[dict] = []
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError(f"top-level JSON structure must be a list of conversations: {path}")
        conversations.extend(data)
    return conversations


def _has_glob(value: str) -> bool:
    return any(char in value for char in "*?[]")


if __name__ == "__main__":
    raise SystemExit(main())
