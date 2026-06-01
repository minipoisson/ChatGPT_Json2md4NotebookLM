import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CliTests(unittest.TestCase):
    def test_cli_writes_numbered_markdown_and_respects_overwrite(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            input_path = tmp_path / "conversations.json"
            output_path = tmp_path / "ChatGPT_History.md"
            input_path.write_text(
                json.dumps(
                    [
                        {
                            "title": "CLI",
                            "create_time": 1,
                            "update_time": 1,
                            "current_node": "m1",
                            "mapping": {
                                "m1": {
                                    "id": "m1",
                                    "message": {
                                        "id": "m1",
                                        "author": {"role": "user"},
                                        "content": {"parts": ["hello"]},
                                        "metadata": {},
                                        "recipient": "all",
                                    },
                                    "parent": None,
                                    "children": [],
                                }
                            },
                        }
                    ]
                ),
                encoding="utf-8",
            )

            command = [
                sys.executable,
                "-m",
                "chatgpt_json2md.cli",
                "--input_file",
                str(input_path),
                "--output_file",
                str(output_path),
            ]
            env = os.environ.copy()
            env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")

            first = subprocess.run(command, cwd=tmp_path, env=env, text=True, capture_output=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertTrue((tmp_path / "ChatGPT_History-01.md").exists())

            second = subprocess.run(command, cwd=tmp_path, env=env, text=True, capture_output=True)
            self.assertNotEqual(second.returncode, 0)

            third = subprocess.run(command + ["--overwrite"], cwd=tmp_path, env=env, text=True, capture_output=True)
            self.assertEqual(third.returncode, 0, third.stderr)

    def test_cli_can_run_as_script_with_split_input_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            samples = tmp_path / "samples"
            samples.mkdir()
            for index, title in enumerate(["One", "Two"]):
                (samples / f"conversations-{index:03d}.json").write_text(
                    json.dumps(
                        [
                            {
                                "title": title,
                                "create_time": index + 1,
                                "update_time": index + 1,
                                "current_node": "m1",
                                "mapping": {
                                    "m1": {
                                        "id": "m1",
                                        "message": {
                                            "id": "m1",
                                            "author": {"role": "user"},
                                            "content": {"parts": [f"hello {title}"]},
                                            "metadata": {},
                                            "recipient": "all",
                                        },
                                        "parent": None,
                                        "children": [],
                                    }
                                },
                            }
                        ]
                    ),
                    encoding="utf-8",
                )

            script = Path(__file__).resolve().parents[1] / "src" / "chatgpt_json2md" / "cli.py"
            command = [
                sys.executable,
                str(script),
                "--input_file",
                str(samples),
                "--output_file",
                str(tmp_path / "ChatGPT_History.md"),
            ]

            result = subprocess.run(command, cwd=tmp_path, text=True, capture_output=True)

            self.assertEqual(result.returncode, 0, result.stderr)
            content = (tmp_path / "ChatGPT_History-01.md").read_text(encoding="utf-8")
            self.assertIn("Conversation: One", content)
            self.assertIn("Conversation: Two", content)
