"""Tests for SRT parser."""

import unittest
import tempfile
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.srt_parser import SRTParser
from core.models import SRTEntry


class TestSRTParser(unittest.TestCase):
    """Test SRTParser class."""

    def setUp(self):
        """Set up test fixtures."""
        self.parser = SRTParser()

    def test_parse_simple_srt(self):
        """Test parsing a simple SRT file."""
        srt_content = """1
00:00:01,000 --> 00:00:04,000
Hello World

2
00:00:05,000 --> 00:00:08,000
Second subtitle
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8') as f:
            f.write(srt_content)
            temp_path = f.name

        try:
            entries = self.parser.parse(temp_path)
            self.assertEqual(len(entries), 2)

            self.assertEqual(entries[0].index, 1)
            self.assertEqual(entries[0].start_time, 1000)
            self.assertEqual(entries[0].end_time, 4000)
            self.assertEqual(entries[0].text, "Hello World")

            self.assertEqual(entries[1].index, 2)
            self.assertEqual(entries[1].text, "Second subtitle")
        finally:
            os.unlink(temp_path)

    def test_parse_multiline_text(self):
        """Test parsing SRT with multiline text."""
        srt_content = """1
00:00:01,000 --> 00:00:04,000
Line 1
Line 2
Line 3

2
00:00:05,000 --> 00:00:08,000
Single line
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8') as f:
            f.write(srt_content)
            temp_path = f.name

        try:
            entries = self.parser.parse(temp_path)
            self.assertEqual(len(entries), 2)
            self.assertEqual(entries[0].text, "Line 1\nLine 2\nLine 3")
            self.assertEqual(entries[1].text, "Single line")
        finally:
            os.unlink(temp_path)

    def test_parse_with_crlf(self):
        """Test parsing SRT with Windows line endings."""
        srt_content = "1\r\n00:00:01,000 --> 00:00:04,000\r\nHello\r\n\r\n2\r\n00:00:05,000 --> 00:00:08,000\r\nWorld\r\n"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8', newline='') as f:
            f.write(srt_content)
            temp_path = f.name

        try:
            entries = self.parser.parse(temp_path)
            self.assertEqual(len(entries), 2)
            self.assertEqual(entries[0].text, "Hello")
            self.assertEqual(entries[1].text, "World")
        finally:
            os.unlink(temp_path)

    def test_add_entry(self):
        """Test adding a new entry."""
        # First create some entries
        self.parser.entries = [
            SRTEntry(index=1, start_time=0, end_time=1000, text="First"),
            SRTEntry(index=2, start_time=2000, end_time=3000, text="Second"),
        ]

        new_entry = self.parser.add_entry(2, 1500, 1800, "Inserted")

        self.assertEqual(len(self.parser.entries), 3)
        self.assertEqual(self.parser.entries[1].text, "Inserted")
        self.assertEqual(self.parser.entries[1].start_time, 1500)

        # Check reindexing
        self.assertEqual(self.parser.entries[0].index, 1)
        self.assertEqual(self.parser.entries[1].index, 2)
        self.assertEqual(self.parser.entries[2].index, 3)

    def test_delete_entry(self):
        """Test deleting an entry."""
        self.parser.entries = [
            SRTEntry(index=1, start_time=0, end_time=1000, text="First"),
            SRTEntry(index=2, start_time=2000, end_time=3000, text="Second"),
            SRTEntry(index=3, start_time=4000, end_time=5000, text="Third"),
        ]

        result = self.parser.delete_entry(2)
        self.assertTrue(result)
        self.assertEqual(len(self.parser.entries), 2)
        self.assertEqual(self.parser.entries[0].index, 1)
        self.assertEqual(self.parser.entries[1].index, 2)
        self.assertEqual(self.parser.entries[1].text, "Third")

    def test_duplicate_entry(self):
        """Test duplicating an entry."""
        self.parser.entries = [
            SRTEntry(index=1, start_time=0, end_time=1000, text="First"),
            SRTEntry(index=2, start_time=2000, end_time=3000, text="Second"),
        ]

        new_entry = self.parser.duplicate_entry(1)
        self.assertIsNotNone(new_entry)
        self.assertEqual(len(self.parser.entries), 3)
        self.assertEqual(self.parser.entries[1].text, "First")
        self.assertEqual(self.parser.entries[1].start_time, 0)

    def test_get_entry(self):
        """Test getting entry by index."""
        self.parser.entries = [
            SRTEntry(index=1, start_time=0, end_time=1000, text="First"),
            SRTEntry(index=2, start_time=2000, end_time=3000, text="Second"),
        ]

        entry = self.parser.get_entry(2)
        self.assertIsNotNone(entry)
        self.assertEqual(entry.text, "Second")

        entry = self.parser.get_entry(99)
        self.assertIsNone(entry)

    def test_save_srt(self):
        """Test saving SRT file."""
        self.parser.entries = [
            SRTEntry(index=1, start_time=1000, end_time=4000, text="Hello"),
            SRTEntry(index=2, start_time=5000, end_time=8000, text="World"),
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8') as f:
            temp_path = f.name

        try:
            result = self.parser.save(temp_path)
            self.assertTrue(result)

            # Read back and verify
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()

            self.assertIn("1\n00:00:01,000 --> 00:00:04,000\nHello", content)
            self.assertIn("2\n00:00:05,000 --> 00:00:08,000\nWorld", content)
        finally:
            os.unlink(temp_path)


if __name__ == '__main__':
    unittest.main()
