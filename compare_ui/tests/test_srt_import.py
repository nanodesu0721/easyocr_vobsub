"""Tests for SRT file import functionality."""

import unittest
import tempfile
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.srt_parser import SRTParser
from core.models import SRTEntry


class TestSRTImport(unittest.TestCase):
    """Test SRT import with various formats and encodings."""

    def setUp(self):
        """Set up test fixtures."""
        self.parser = SRTParser()

    def test_import_utf8_with_unicode(self):
        """Test importing UTF-8 file with Unicode characters."""
        srt_content = """1
00:00:01,000 --> 00:00:04,000
Hello World 你好世界

2
00:00:05,000 --> 00:00:09,000
Second subtitle with Unicode: ñoño 日本語

3
00:00:10,000 --> 00:00:14,000
Third subtitle
with multiple lines
and special chars: émojis 🎬🎭
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8') as f:
            f.write(srt_content)
            temp_path = f.name

        try:
            entries = self.parser.parse(temp_path)
            self.assertEqual(len(entries), 3)
            self.assertEqual(self.parser.encoding.lower(), 'utf-8')

            # Check Unicode content
            self.assertIn('你好世界', entries[0].text)
            self.assertIn('日本語', entries[1].text)
            self.assertIn('🎬', entries[2].text)
        finally:
            os.unlink(temp_path)

    def test_import_with_html_tags(self):
        """Test importing SRT with HTML tags."""
        srt_content = """1
00:00:01,000 --> 00:00:04,000
<b>Bold text</b> and <i>italic</i>

2
00:00:05,000 --> 00:00:08,000
<font color="red">Colored text</font>
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8') as f:
            f.write(srt_content)
            temp_path = f.name

        try:
            entries = self.parser.parse(temp_path)
            self.assertEqual(len(entries), 2)
            self.assertIn('<b>', entries[0].text)
            self.assertIn('<font', entries[1].text)
        finally:
            os.unlink(temp_path)

    def test_import_with_quotes_and_special_chars(self):
        """Test importing SRT with quotes and special characters."""
        srt_content = """1
00:00:01,000 --> 00:00:04,000
Text with "double quotes" and 'single quotes'

2
00:00:05,000 --> 00:00:08,000
Special chars: & < > © ® ™
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8') as f:
            f.write(srt_content)
            temp_path = f.name

        try:
            entries = self.parser.parse(temp_path)
            self.assertEqual(len(entries), 2)
            self.assertIn('"double quotes"', entries[0].text)
            self.assertIn("'single quotes'", entries[0].text)
            self.assertIn('&', entries[1].text)
        finally:
            os.unlink(temp_path)

    def test_import_large_file(self):
        """Test importing a larger SRT file."""
        lines = []
        for i in range(1, 101):
            start_ms = (i - 1) * 5000
            end_ms = start_ms + 4000
            start_str = f"{start_ms // 3600000:02d}:{(start_ms % 3600000) // 60000:02d}:{(start_ms % 60000) // 1000:02d},{start_ms % 1000:03d}"
            end_str = f"{end_ms // 3600000:02d}:{(end_ms % 3600000) // 60000:02d}:{(end_ms % 60000) // 1000:02d},{end_ms % 1000:03d}"
            lines.append(f"{i}")
            lines.append(f"{start_str} --> {end_str}")
            lines.append(f"Subtitle line {i}")
            lines.append("")

        srt_content = "\n".join(lines)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8') as f:
            f.write(srt_content)
            temp_path = f.name

        try:
            entries = self.parser.parse(temp_path)
            self.assertEqual(len(entries), 100)
            self.assertEqual(entries[0].text, "Subtitle line 1")
            self.assertEqual(entries[99].text, "Subtitle line 100")
            self.assertEqual(entries[99].index, 100)
        finally:
            os.unlink(temp_path)

    def test_import_with_empty_lines(self):
        """Test importing SRT with extra empty lines."""
        srt_content = """1
00:00:01,000 --> 00:00:04,000
First subtitle


2
00:00:05,000 --> 00:00:08,000
Second subtitle



3
00:00:09,000 --> 00:00:12,000
Third subtitle
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8') as f:
            f.write(srt_content)
            temp_path = f.name

        try:
            entries = self.parser.parse(temp_path)
            self.assertEqual(len(entries), 3)
        finally:
            os.unlink(temp_path)

    def test_import_with_dot_separator(self):
        """Test importing SRT with dot (.) instead of comma (,) in time."""
        srt_content = """1
00:00:01.000 --> 00:00:04.000
First subtitle with dot separator

2
00:00:05.000 --> 00:00:08.000
Second subtitle
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8') as f:
            f.write(srt_content)
            temp_path = f.name

        try:
            entries = self.parser.parse(temp_path)
            self.assertEqual(len(entries), 2)
            self.assertEqual(entries[0].start_time, 1000)
            self.assertEqual(entries[0].end_time, 4000)
        finally:
            os.unlink(temp_path)

    def test_import_single_entry(self):
        """Test importing SRT with only one entry."""
        srt_content = """1
00:00:01,000 --> 00:00:04,000
Only one subtitle entry
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8') as f:
            f.write(srt_content)
            temp_path = f.name

        try:
            entries = self.parser.parse(temp_path)
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].index, 1)
            self.assertEqual(entries[0].text, "Only one subtitle entry")
        finally:
            os.unlink(temp_path)

    def test_import_with_positioning(self):
        """Test importing SRT with positioning tags."""
        srt_content = """1
00:00:01,000 --> 00:00:04,000 X1:40 X2:680 Y1:500 Y2:560
Subtitle with positioning

2
00:00:05,000 --> 00:00:08,000
Normal subtitle
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8') as f:
            f.write(srt_content)
            temp_path = f.name

        try:
            entries = self.parser.parse(temp_path)
            self.assertEqual(len(entries), 2)
            # Time should still be parsed correctly despite positioning
            self.assertEqual(entries[0].start_time, 1000)
            self.assertEqual(entries[0].end_time, 4000)
        finally:
            os.unlink(temp_path)


class TestSRTImportEdgeCases(unittest.TestCase):
    """Test edge cases for SRT import."""

    def setUp(self):
        """Set up test fixtures."""
        self.parser = SRTParser()

    def test_empty_file(self):
        """Test importing empty SRT file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8') as f:
            f.write("")
            temp_path = f.name

        try:
            entries = self.parser.parse(temp_path)
            self.assertEqual(len(entries), 0)
        finally:
            os.unlink(temp_path)

    def test_whitespace_only_file(self):
        """Test importing SRT file with only whitespace."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8') as f:
            f.write("   \n\n   \n")
            temp_path = f.name

        try:
            entries = self.parser.parse(temp_path)
            self.assertEqual(len(entries), 0)
        finally:
            os.unlink(temp_path)

    def test_invalid_time_format(self):
        """Test handling of invalid time format."""
        srt_content = """1
00:00:01,000 --> invalid
This should be skipped

2
00:00:05,000 --> 00:00:08,000
Valid subtitle
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8') as f:
            f.write(srt_content)
            temp_path = f.name

        try:
            entries = self.parser.parse(temp_path)
            # Should only parse the valid entry
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].text, "Valid subtitle")
        finally:
            os.unlink(temp_path)


if __name__ == '__main__':
    unittest.main()
