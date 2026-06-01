import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from chatgpt_json2md.converter import convert_conversations


def message_node(node_id, role, text, parent=None, *, recipient="all", metadata=None, create_time=0):
    return {
        "id": node_id,
        "message": {
            "id": f"msg-{node_id}",
            "author": {"role": role},
            "create_time": create_time,
            "content": {"content_type": "text", "parts": [text]},
            "metadata": metadata or {},
            "recipient": recipient,
        },
        "parent": parent,
        "children": [],
    }


class ConverterTests(unittest.TestCase):
    def test_current_node_path_uses_visible_branch_only(self):
        conv = {
            "title": "Branching",
            "create_time": 1,
            "update_time": 2,
            "current_node": "assistant-final",
            "mapping": {
                "root": {"id": "root", "message": None, "parent": None, "children": ["user"]},
                "user": message_node("user", "user", "Question", "root", create_time=1),
                "assistant-old": message_node("assistant-old", "assistant", "Old answer", "user", create_time=2),
                "assistant-final": message_node("assistant-final", "assistant", "Final answer", "user", create_time=3),
            },
        }

        result = convert_conversations([conv])

        self.assertEqual(len(result.blocks), 1)
        self.assertIn("Question", result.blocks[0])
        self.assertIn("- Time: 1970-01-01 00:00:01 UTC", result.blocks[0])
        self.assertIn("Final answer", result.blocks[0])
        self.assertNotIn("Old answer", result.blocks[0])

    def test_skips_system_tool_hidden_empty_and_non_all_recipient_messages(self):
        conv = {
            "title": "Filtering",
            "create_time": 1,
            "update_time": 1,
            "current_node": "assistant-visible",
            "mapping": {
                "root": {"id": "root", "message": None, "parent": None, "children": []},
                "system": message_node("system", "system", "system text", "root"),
                "tool": message_node("tool", "assistant", "tool call", "system", recipient="python"),
                "hidden": message_node(
                    "hidden",
                    "assistant",
                    "hidden text",
                    "tool",
                    metadata={"is_visually_hidden_from_conversation": True},
                ),
                "empty": message_node("empty", "user", "   ", "hidden"),
                "assistant-visible": message_node("assistant-visible", "assistant", "Visible", "empty"),
            },
        }

        result = convert_conversations([conv])

        block = result.blocks[0]
        self.assertIn("Visible", block)
        self.assertNotIn("system text", block)
        self.assertNotIn("tool call", block)
        self.assertNotIn("hidden text", block)

    def test_extracts_text_parts_even_when_content_type_is_not_text(self):
        conv = {
            "title": "Multimodal",
            "create_time": 1,
            "update_time": 1,
            "current_node": "assistant",
            "mapping": {
                "root": {"id": "root", "message": None, "parent": None, "children": []},
                "user": message_node("user", "user", "hello", "root"),
                "assistant": message_node("assistant", "assistant", "", "user"),
            },
        }
        conv["mapping"]["assistant"]["message"]["content"] = {
            "content_type": "multimodal_text",
            "parts": [{"text": "text part"}, {"image_url": "ignored"}],
        }

        result = convert_conversations([conv])

        self.assertIn("text part", result.blocks[0])

    def test_conversations_are_sorted_by_update_then_create_then_input_order(self):
        conv_a = {
            "title": "B",
            "create_time": 1,
            "update_time": 20,
            "current_node": "a",
            "mapping": {"a": message_node("a", "user", "second")},
        }
        conv_b = {
            "title": "A",
            "create_time": 1,
            "update_time": 10,
            "current_node": "b",
            "mapping": {"b": message_node("b", "user", "first")},
        }
        conv_c = {
            "title": "C",
            "create_time": 30,
            "current_node": "c",
            "mapping": {"c": message_node("c", "user", "third")},
        }

        result = convert_conversations([conv_a, conv_c, conv_b])

        joined = "\n".join(result.blocks)
        self.assertLess(joined.index("Conversation: A"), joined.index("Conversation: B"))
        self.assertLess(joined.index("Conversation: B"), joined.index("Conversation: C"))
