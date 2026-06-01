# ChatGPT Json2md for NotebookLM

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/github/license/minipoisson/ChatGPT_Json2md4NotebookLM)
![Release](https://img.shields.io/github/v/release/minipoisson/ChatGPT_Json2md4NotebookLM)

[日本語READMEはこちら](README.ja.md)

Convert ChatGPT's exported `conversations.json` into numbered Markdown files that are easier to import into NotebookLM.

This script is a ChatGPT-focused companion to [Gemini_Json2md4NotebookLM](https://github.com/minipoisson/Gemini_Json2md4NotebookLM) and [Claude_Json2md4NotebookLM](https://github.com/minipoisson/Claude_Json2md4NotebookLM), sharing the same goal: making AI chat exports easier to import into NotebookLM.

The initial version intentionally does not support incremental updates; each run generates a fresh Markdown set from the full input JSON.

## Features

- Restores the visible ChatGPT conversation path from the `mapping` / `current_node` structure
- Outputs `title`, `create_time`, and `update_time` for each conversation
- Keeps only visible `user` and `assistant` messages
- Skips `system`, `tool`, hidden, empty, and non-`all` recipient messages
- Escapes literal `<` and `>` in titles and message text so NotebookLM does not treat them as HTML
- Converts ChatGPT UI citation/image markers into readable notes such as `[Web citations: 3 references]`
- Splits output into numbered Markdown files such as `ChatGPT_History-01.md`
- Uses a 1 MB default split limit
- Requires only the Python standard library

## Requirements

- Python 3.9 or higher

## Usage

1. Export your ChatGPT data from ChatGPT settings.
2. Extract the export archive and locate `conversations.json`.
3. Run the converter from this repository root:

```powershell
python src\chatgpt_json2md\cli.py --input conversations.json --output_file ChatGPT_History.md --limit 1000000
```

If you prefer `python -m`, set `PYTHONPATH` to `src` first:

```powershell
$env:PYTHONPATH="src"
python -m chatgpt_json2md.cli --input conversations.json --output_file ChatGPT_History.md
```

On bash:

```bash
PYTHONPATH=src python -m chatgpt_json2md.cli --input conversations.json --output_file ChatGPT_History.md
```

## Options

| Option | Default | Description |
| --- | --- | --- |
| `--input`, `--input_file` | `conversations.json` | Path, directory, glob pattern, or multiple paths for ChatGPT conversations JSON |
| `--output_file` | `ChatGPT_History.md` | Base name for output Markdown files |
| `--limit` | `1000000` | Maximum UTF-8 bytes per output file |
| `--overwrite` | `false` | Overwrite existing numbered output files |

For newer exports split into files such as `conversations-000.json` through `conversations-005.json`, point `--input_file` at the directory:

```bash
PYTHONPATH=src python -m chatgpt_json2md.cli --input samples --output_file ChatGPT_History.md
```

Or pass a glob pattern:

```bash
PYTHONPATH=src python -m chatgpt_json2md.cli --input "samples/conversations-*.json" --output_file ChatGPT_History.md
```

You can also run the CLI file directly from an IDE or PowerShell:

```powershell
python src\chatgpt_json2md\cli.py --input samples --output_file ChatGPT_History.md
```

If `--output_file` is `ChatGPT_History.md`, generated files are named:

```text
ChatGPT_History-01.md
ChatGPT_History-02.md
ChatGPT_History-03.md
```

If any generated output path already exists, the command exits with an error unless `--overwrite` is specified.

## Markdown Format

Each file starts with an archive header:

```markdown
# ChatGPT Conversation History

Generated at: 2026-05-09 13:30:00 UTC
```

Each conversation is rendered as:

```markdown
## Conversation: Example title

- Created: 2023-04-27 12:34:10 UTC
- Updated: 2023-04-28 09:10:50 UTC

### User

- Time: 2023-04-27 12:35:00 UTC

User message text.

### Assistant

- Time: 2023-04-27 12:36:10 UTC

Assistant message text.

---
```

## Notes

- Conversations are sorted by `update_time`, then `create_time`, then their original input order.
- Each message includes its own `message.create_time` as `- Time:` when available.
- The visible path is restored by walking from `current_node` back through `parent` links.
- Literal `<` and `>` are escaped even inside code blocks. This is intentional for NotebookLM ingestion.
- ChatGPT UI markers such as `cite...` and `i...` are converted to short notes. Internal `turn...` IDs are omitted by default.
- A single conversation larger than `--limit` is kept whole in one file and reported as exceeding the limit.
- Incremental append behavior and `last_entry_time.txt` are outside the initial version.

## Development

Run tests with:

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

See [docs/SPEC.md](docs/SPEC.md) for the implementation specification.

## Related

- [Gemini_Json2md4NotebookLM](https://github.com/minipoisson/Gemini_Json2md4NotebookLM) - Gemini version of this tool
- [Claude_Json2md4NotebookLM](https://github.com/minipoisson/Claude_Json2md4NotebookLM) - Claude version of this tool

## License

MIT License. See [LICENSE](LICENSE) for details.
