# ChatGPT Json2md for NotebookLM 初期版仕様

## 目的

ChatGPT のデータエクスポートに含まれる `conversations.json` を、NotebookLM に読み込ませやすい Markdown ファイルへ変換する。

初期版では、Claude 版・Gemini 版の設計思想を引き継ぎつつ、ChatGPT の `mapping` 構造に対応する。増分更新機能は含めず、実行ごとに入力 JSON 全体から Markdown 一式を生成する。

## 対象範囲

### 含める機能

- `conversations.json` の読み込み
- ChatGPT の `mapping` 構造から会話の主経路を復元
- `user` / `assistant` 発言の時系列 Markdown 化
- `title`, `create_time`, `update_time` の出力
- スレッド内の各メッセージの `message.create_time` の出力
- HTML タグ風の文字列を削除せず、NotebookLM に読み飛ばされない形で保持
- ChatGPT UI 用の引用・画像マーカーを NotebookLM 向けの可読な注記へ正規化
- UTF-8 バイト数ベースの Markdown ファイル分割
- 出力ファイル名への `-01` から始まる連番付与
- NotebookLM で読みやすい会話単位の区切り
- 基本的なエラー処理

### 初期版では含めない機能

- 増分更新
- `last_entry_time.txt` の作成・読み込み
- 既存 Markdown への差分追記
- メッセージ途中での強制分割
- 画像・添付ファイル・音声などのメディア抽出
- tool 実行結果や hidden message の出力
- Gemini export の `safeHtmlItem` のような HTML 構造の Markdown 再構成
- 外部ライブラリへの依存

## 入力仕様

入力は ChatGPT データエクスポートに含まれる `conversations.json`、または `conversations-000.json` のように分割された JSON ファイル群とする。入力ファイルは `--input_file` で指定する。

`--input_file` には、単一ファイル、複数ファイル、ディレクトリ、glob パターンを指定できる。`--input` は `--input_file` の別名として扱う。

ディレクトリが指定された場合は、そのディレクトリ内の `conversations*.json` をファイル名昇順で読み込む。

想定するトップレベル構造は、会話オブジェクトの配列。

```json
[
  {
    "title": "Conversation title",
    "create_time": 1682600000.0,
    "update_time": 1682606050.0,
    "mapping": {},
    "current_node": "node-id",
    "id": "conversation-id"
  }
]
```

各会話では、主に次のフィールドを利用する。

| Field | 用途 |
| --- | --- |
| `title` | 会話見出し |
| `create_time` | 作成日時 |
| `update_time` | 更新日時 |
| `mapping` | メッセージノード群 |
| `current_node` | 現在表示されている会話末尾ノード |
| `id` | 必要に応じた警告表示・デバッグ情報 |

## 会話の並び順

出力する会話は、NotebookLM で時系列に読みやすいように昇順で並べる。

並び替えキーは次の優先順位とする。

1. `update_time`
2. `create_time`
3. 入力 JSON 内での元の出現順

`update_time` または `create_time` が欠損または不正な場合は、次の優先順位へフォールバックする。

## ChatGPT mapping 復元仕様

ChatGPT の `mapping` は単純な配列ではなく、ノードの親子関係で構成される。

各ノードは概ね次の構造を持つ。

```json
{
  "id": "node-id",
  "message": {},
  "parent": "parent-node-id",
  "children": ["child-node-id"]
}
```

初期版では、NotebookLM に読み込ませる本文として、ユーザーが最終的に見ている主経路を採用する。

復元手順は次の通り。

1. 会話オブジェクトの `current_node` を起点にする。
2. `parent` をたどって root 方向へ進む。
3. たどったノード列を逆順にする。
4. 逆順にしたノード列から出力対象メッセージだけを抽出する。

`current_node` が欠損している、または `mapping` 内に存在しない場合は、フォールバックとして `mapping` 内のメッセージを `message.create_time` 昇順で処理する。

循環参照を検出した場合は、その会話の復元を中断し、可能な範囲で警告を出す。

## メッセージ抽出仕様

出力対象は原則として `author.role` が `user` または `assistant` のメッセージのみとする。

### 出力する role

| role | Markdown 表示 |
| --- | --- |
| `user` | `### User` |
| `assistant` | `### Assistant` |

### スキップするメッセージ

- `message` が `null`
- `author.role` が `system`
- `author.role` が `tool`
- `author.role` が空または不明
- `recipient` が存在し、かつ `all` 以外
- `content.parts` が空
- 抽出した本文が空白のみ
- hidden 系メタデータを持つメッセージ

hidden 判定では、少なくとも次のようなメタデータを考慮する。

- `metadata.is_visually_hidden_from_conversation == true`
- `metadata.is_hidden == true`

### content 抽出

初期版では、`content.content_type` が `text` 以外の場合でも、`content.parts` にテキストとして扱える part が含まれていれば抽出対象とする。

`content.parts` がリストの場合、次のルールで本文を取り出す。

- 要素が文字列なら、本文候補として利用する。
- 要素が辞書で `text` キーを持つ場合は、その値を利用する。
- その他の要素はスキップする。

複数 part がある場合は、空でない part を改行で結合する。

### HTML タグ風文字列の扱い

ChatGPT の `conversations.json` では、Gemini export の `safeHtmlItem` のように、モデル応答が HTML 構造として保存されているとは限らない。

`content.parts` に含まれる `<div>`, `<p>`, `<script>`, `<xml>` などのタグ風文字列は、次のような会話本文そのものとして扱う。

- ユーザーが貼り付けた HTML / XML / JSX
- ChatGPT が回答したコード例
- Markdown 内に含まれるインライン HTML
- 説明文中のタグ名

そのため、初期版では HTML タグを削除しない。また、Gemini 版のように HTML 構造を積極的に Markdown へ再構成する処理も行わない。

NotebookLM が HTML タグで囲まれた部分を読み飛ばすことを防ぐため、Markdown 出力時にはタイトルおよびメッセージ本文中のリテラルな `<` と `>` を HTML entity に変換する。

例:

```text
<div>Hello</div>
```

Markdown 出力:

```markdown
&lt;div&gt;Hello&lt;/div&gt;
```

この処理は、タグ風文字列を NotebookLM から見える本文として保持するためのエスケープであり、HTML の意味解釈やサニタイズを目的としない。

初期版では NotebookLM での読み取りを優先するため、Markdown の fenced code block 内に含まれる `<` と `>` も同じくエスケープ対象とする。

### ChatGPT UI artifact の扱い

ChatGPT の `conversations.json` には、本文中に ChatGPT UI 用の特殊マーカーが含まれる場合がある。

例:

```text
citeturn605931search0turn605931search1
iturn0image1turn0image2
```

これらは ChatGPT の画面上では、点線下線の引用リンク、画像参照、ボタン状の参照などとして表示されることがある。しかし Markdown や NotebookLM では意味を持たず、内部 ID や私用領域文字が検索ノイズになりやすい。

初期版では、利用可能な通常本文は保持しつつ、ChatGPT UI 用マーカーを次のような可読な注記へ変換する。

| 入力種別 | Markdown 出力 |
| --- | --- |
| `cite...` | `[Web citations: N references]` |
| `i...` | `[Image references: N images]` |
| その他の同形式マーカー | `[ChatGPT UI artifact: KIND, N items]` |

`turn...search0` や `turn...image1` のような内部 ID は、初期版では出力しない。

``, ``, `` のような単独の ChatGPT UI 制御文字は、本文として有用な情報を持たないため削除する。

例:

```text
iturn0image1turn0image2以下に説明します。
```

Markdown 出力:

```markdown
[Image references: 2 images]

以下に説明します。
```

## 日時仕様

ChatGPT の `create_time`, `update_time`, `message.create_time` は Unix epoch 秒の float を想定する。

Markdown には UTC の人間可読形式で出力する。

例:

```text
2023-04-27 12:34:10 UTC
```

日時が欠損または不正な場合は、空文字ではなく `Unknown` と表示する。

各メッセージの `message.create_time` は、そのメッセージ見出しの直下に `- Time: ...` として出力する。

## Markdown 出力仕様

各出力ファイルの先頭には、アーカイブ全体のヘッダーを置く。

```markdown
# ChatGPT Conversation History

Generated at: 2026-05-09 13:30:00 UTC

```

各会話は次の形式で出力する。

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

タイトルが空の場合は `(Untitled)` を利用する。

タイトル内の改行はスペースに置換する。

タイトル中の `<` と `>` は、HTML タグとして解釈されないよう、それぞれ `&lt;` と `&gt;` にエスケープする。

本文は Markdown として過剰に加工しない。NotebookLM での読み取りやすさを優先し、連続する 3 個以上の空行は 2 個に正規化する。

本文中の `<` と `>` は、HTML タグとして解釈されないよう、それぞれ `&lt;` と `&gt;` にエスケープする。

## ファイル分割仕様

出力ファイルは `--output_file` で指定されたファイル名をベースに、末尾へ `-NN` を付ける。省略時のデフォルトは `ChatGPT_History.md` とする。

例:

```text
ChatGPT_History-01.md
ChatGPT_History-02.md
ChatGPT_History-03.md
```

分割判定は UTF-8 エンコード後のバイト数で行う。

出力ファイルのサイズの上限は `--limit` の後に byte 数を指定する。

会話ブロックの途中では分割しない。次の会話ブロックを追加すると上限を超える場合、新しいファイルへ移る。

ただし、単一の会話ブロックだけで上限を超える場合は、その会話ブロックを 1 ファイルに出力し、警告を表示する。初期版ではメッセージ途中分割を行わない。

### 既存出力ファイルの扱い

初期版では、既存 Markdown への差分追記は行わない。

出力予定のファイルと同名のファイルが既に存在する場合、`--overwrite` が指定されていなければエラーメッセージを表示し、非 0 の終了コードで終了する。

`--overwrite` が指定されている場合は、出力予定の同名ファイルを上書きする。

## CLI 仕様

実行例:

```bash
python src/chatgpt_json2md/cli.py --input conversations.json --output_file ChatGPT_History.md --limit 1000000
```

初期版で提供するオプション:

| Option | Default | Description |
| --- | --- | --- |
| `--input`, `--input_file` | `conversations.json` | ChatGPT export の入力 JSON。複数指定、ディレクトリ、glob パターンも可 |
| `--output_file` | `ChatGPT_History.md` | 出力 Markdown のベースファイル名 |
| `--limit` | `1000000` | 1 ファイルあたりの最大バイト数 |
| `--overwrite` | `false` | 既存の同名出力ファイルを上書きする |

## エラー処理仕様

### 入力ファイルが存在しない

エラーメッセージを表示し、非 0 の終了コードで終了する。

### JSON として不正

JSON decode error を表示し、非 0 の終了コードで終了する。

### トップレベルが配列ではない

想定外の構造であることを表示し、非 0 の終了コードで終了する。

### 出力予定ファイルが既に存在する

`--overwrite` が指定されていなければ、エラーメッセージを表示し、非 0 の終了コードで終了する。

`--overwrite` が指定されていれば、既存の同名ファイルを上書きする。

### 個別会話の構造が不正

可能な限り処理を継続する。

該当会話をスキップした場合は、会話タイトルまたは `id` を含む警告を表示する。

### メッセージノードが一部壊れている

壊れたノードをスキップし、可能な範囲で会話を出力する。

## 実装方針

初期版は標準ライブラリのみで実装する。

推奨構成:

```text
src/
  chatgpt_json2md/
    __init__.py
    cli.py
    converter.py
    markdown.py
    splitter.py
    timeutils.py

tests/
  test_converter.py
  test_markdown.py
  test_splitter.py
  fixtures/

docs/
  SPEC.md

README.md
```

各モジュールの責務:

| Module | Responsibility |
| --- | --- |
| `cli.py` | CLI、ファイル読み書き、終了コード |
| `converter.py` | conversations.json から会話本文を抽出 |
| `markdown.py` | Markdown 文字列の生成 |
| `splitter.py` | バイト数ベースのファイル分割 |
| `timeutils.py` | epoch 秒から UTC 表示への変換 |

## テスト方針

### converter

- `current_node` から parent をたどって時系列復元できること
- 分岐がある場合に current path のみ採用すること
- `system`, `tool`, hidden, 空メッセージをスキップすること
- `recipient` が存在し、かつ `all` 以外のメッセージをスキップすること
- `message: null` の root ノードを無視すること
- `content.parts` の文字列を本文化できること
- `content_type` が `text` 以外でも、テキスト part があれば抽出できること
- `parts` に辞書や不明要素が混ざっても落ちないこと
- HTML タグ風文字列を削除せず、`<` と `>` をエスケープして保持すること
- ChatGPT UI 用の `cite` / `i` マーカーを件数付き注記へ変換すること
- ChatGPT UI 用の単独制御文字を削除すること
- 会話全体が `update_time`, `create_time`, 入力順の優先順位で並ぶこと

### markdown

- `title`, `create_time`, `update_time` が出力されること
- 各メッセージの `message.create_time` が `- Time:` として出力されること
- 空タイトルが `(Untitled)` になること
- タイトル中の `<div>` が `&lt;div&gt;` として出力されること
- `### User` と `### Assistant` が出力されること
- 会話末尾に `---` が入ること
- 連続空行が正規化されること
- 本文中の `<div>text</div>` が `&lt;div&gt;text&lt;/div&gt;` として出力されること

### splitter

- `ChatGPT_History.md` から `ChatGPT_History-01.md` が生成されること
- 複数ブロックが `--limit` に従って分割されること
- UTF-8 バイト数でサイズ判定されること
- 単一ブロックが上限超過しても内容を破壊しないこと

### cli

- 入力ファイルなしで非 0 終了すること
- `conversations-000.json` 形式の複数ファイルを読み込めること
- `cli.py` を直接実行しても import error にならないこと
- JSON decode error で非 0 終了すること
- 正常系で Markdown ファイルが生成されること
- `--limit` 指定が反映されること
- 既存の同名出力ファイルがあり、`--overwrite` がない場合は非 0 終了すること
- 既存の同名出力ファイルがあり、`--overwrite` がある場合は上書きすること
