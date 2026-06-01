import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from chatgpt_json2md.splitter import ensure_writable_outputs, numbered_output_path, split_blocks


class SplitterTests(unittest.TestCase):
    def test_numbered_output_path_starts_at_01(self):
        self.assertEqual(numbered_output_path("ChatGPT_History.md", 1).name, "ChatGPT_History-01.md")

    def test_split_blocks_uses_utf8_bytes_and_keeps_blocks_whole(self):
        header = "# Header\n\n"
        blocks = ["## A\n\nああ\n\n---\n\n", "## B\n\nbbb\n\n---\n\n"]

        outputs = split_blocks(blocks, "ChatGPT_History.md", len((header + blocks[0]).encode("utf-8")), header)

        self.assertEqual(len(outputs), 2)
        self.assertIn("## A", outputs[0].content)
        self.assertIn("## B", outputs[1].content)

    def test_single_oversized_block_is_written_and_flagged(self):
        outputs = split_blocks(["x" * 20], "out.md", 10, "# H\n\n")

        self.assertEqual(len(outputs), 1)
        self.assertTrue(outputs[0].exceeds_limit)

    def test_existing_output_requires_overwrite(self):
        with TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "out.md"
            outputs = split_blocks(["body"], target, 100, "header")
            outputs[0].path.write_text("old", encoding="utf-8")

            with self.assertRaises(FileExistsError):
                ensure_writable_outputs(outputs, overwrite=False)

            ensure_writable_outputs(outputs, overwrite=True)
