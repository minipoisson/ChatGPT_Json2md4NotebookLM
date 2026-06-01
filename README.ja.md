# ChatGPT Json2md for NotebookLM

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/github/license/minipoisson/ChatGPT_Json2md4NotebookLM)
![Release](https://img.shields.io/github/v/release/minipoisson/ChatGPT_Json2md4NotebookLM)

[English README](README.md)

ChatGPT のデータエクスポートに含まれる `conversations.json` または `conversations-000.json` のような分割 JSON を、NotebookLM に読み込ませやすい Markdown ファイルへ変換する Python ツールです。

[Gemini_Json2md4NotebookLM](https://github.com/minipoisson/Gemini_Json2md4NotebookLM) および [Claude_Json2md4NotebookLM](https://github.com/minipoisson/Claude_Json2md4NotebookLM) の姉妹ツールとして、AI チャット履歴を NotebookLM に取り込みやすくすることを目的としています。

初期版では増分更新には対応していません。実行ごとに入力 JSON 全体から Markdown 一式を生成します。

## 主な機能

- ChatGPT export の `mapping` / `current_node` 構造から、表示中の会話経路を復元
- 会話ごとに `title`, `create_time`, `update_time` を出力
- 各メッセージごとに `message.create_time` を `- Time:` として出力
- 表示対象の `user` / `assistant` メッセージのみを保持
- `system`, `tool`, hidden, 空メッセージ, `recipient` が `all` 以外のメッセージをスキップ
- NotebookLM に HTML として読み飛ばされないよう、タイトルと本文中の `<` / `>` をエスケープ
- ChatGPT UI 用の引用・画像マーカーを `[Web citations: 3 references]` のような可読な注記へ変換
- `ChatGPT_History-01.md` のような連番 Markdown へ分割出力
- デフォルトの分割上限は 1 MB
- 実行時依存は Python 標準ライブラリのみ

## 必要環境

- Python 3.9 以上

## 使い方

1. ChatGPT の設定画面からデータをエクスポートします。
2. エクスポート ZIP を展開し、`conversations.json` または `conversations-000.json` などの分割ファイルを確認します。
3. このリポジトリのルートで実行します。

PowerShell で単一ファイルを変換する例:

```powershell
python src\chatgpt_json2md\cli.py --input conversations.json --output_file ChatGPT_History.md --limit 1000000
```

分割ファイルをまとめて変換する例:

```powershell
python src\chatgpt_json2md\cli.py --input .\samples\conversations-*.json --output_file ChatGPT_History.md
```

既存の出力ファイルを上書きする場合:

```powershell
python src\chatgpt_json2md\cli.py --input .\samples\conversations-*.json --output_file ChatGPT_History.md --overwrite
```

`python -m` で実行する場合は、先に `PYTHONPATH` を設定します。

```powershell
$env:PYTHONPATH="src"
python -m chatgpt_json2md.cli --input conversations.json --output_file ChatGPT_History.md
```

## オプション

| Option | Default | Description |
| --- | --- | --- |
| `--input`, `--input_file` | `conversations.json` | 入力 JSON。単一ファイル、複数ファイル、ディレクトリ、glob パターンを指定可能 |
| `--output_file` | `ChatGPT_History.md` | 出力 Markdown のベースファイル名 |
| `--limit` | `1000000` | 1 ファイルあたりの最大 UTF-8 バイト数 |
| `--overwrite` | `false` | 既存の同名出力ファイルを上書き |

`--output_file` に `ChatGPT_History.md` を指定した場合、生成ファイル名は次のようになります。

```text
ChatGPT_History-01.md
ChatGPT_History-02.md
ChatGPT_History-03.md
```

既に同名の出力予定ファイルが存在する場合、`--overwrite` が指定されていなければエラー終了します。

## Markdown 出力例

```markdown
# ChatGPT Conversation History

Generated at: 2026-05-09 13:30:00 UTC

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

## 注意

- 会話は `update_time`, `create_time`, 入力順の優先順位で時系列に並びます。
- 会話本文は `current_node` から `parent` をたどって復元します。
- `<` / `>` はコードブロック内も含めてエスケープされます。NotebookLM での読み取りを優先するためです。
- `cite...` や `i...` のような ChatGPT UI マーカーは短い注記に変換され、内部の `turn...` ID は初期版では出力しません。
- 1 つの会話が `--limit` を超える場合、その会話は分割せず 1 ファイルに保持し、警告を表示します。
- 増分更新や `last_entry_time.txt` は初期版の対象外です。

## 開発

テスト実行:

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

実装仕様は [docs/SPEC.md](docs/SPEC.md) を参照してください。

## 関連

- [Gemini_Json2md4NotebookLM](https://github.com/minipoisson/Gemini_Json2md4NotebookLM) - Gemini 版
- [Claude_Json2md4NotebookLM](https://github.com/minipoisson/Claude_Json2md4NotebookLM) - Claude 版

## ライセンス

MIT License. 詳細は [LICENSE](LICENSE) を参照してください。
