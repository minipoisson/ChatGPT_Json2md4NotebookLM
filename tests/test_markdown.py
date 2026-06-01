import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from chatgpt_json2md.markdown import ChatMessage, Conversation, render_conversation


class MarkdownTests(unittest.TestCase):
    def test_render_conversation_escapes_title_and_body_angle_brackets(self):
        conversation = Conversation(
            title="<div>Title</div>",
            create_time=1682606050,
            update_time=1682607050,
            messages=[ChatMessage("user", "Use <span>inline</span> HTML", 1682606150)],
        )

        rendered = render_conversation(conversation)

        self.assertIn("Conversation: &lt;div&gt;Title&lt;/div&gt;", rendered)
        self.assertIn("- Time: 2023-04-27 14:35:50 UTC", rendered)
        self.assertIn("Use &lt;span&gt;inline&lt;/span&gt; HTML", rendered)

    def test_render_conversation_normalizes_empty_title_and_blank_lines(self):
        conversation = Conversation(
            title="",
            create_time=None,
            update_time=None,
            messages=[ChatMessage("assistant", "one\n\n\n\n two")],
        )

        rendered = render_conversation(conversation)

        self.assertIn("Conversation: (Untitled)", rendered)
        self.assertIn("- Created: Unknown", rendered)
        self.assertIn("- Time: Unknown", rendered)
        self.assertIn("one\n\n two", rendered)
        self.assertNotIn("\n\n\n\n", rendered)

    def test_render_conversation_normalizes_chatgpt_ui_artifacts(self):
        conversation = Conversation(
            title="Artifacts",
            create_time=None,
            update_time=None,
            messages=[
                ChatMessage(
                    "assistant",
                    "\ue200i\ue202turn0image1\ue202turn0image2\ue201"
                    "\ue203以下に説明します。\ue204\ue206\n"
                    "\ue200cite\ue202turn1search0\ue202turn1search1\ue202turn1search2\ue201",
                )
            ],
        )

        rendered = render_conversation(conversation)

        self.assertIn("[Image references: 2 images]", rendered)
        self.assertIn("以下に説明します。", rendered)
        self.assertIn("[Web citations: 3 references]", rendered)
        self.assertNotIn("\ue200", rendered)
        self.assertNotIn("\ue202", rendered)
        self.assertNotIn("turn1search0", rendered)
