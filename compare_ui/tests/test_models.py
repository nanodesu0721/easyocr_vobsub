"""Tests for data models."""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.models import SubtitleEntry, VobSubEntry, SRTEntry


class TestSubtitleEntry(unittest.TestCase):
    """Test SubtitleEntry base class."""

    def test_duration_calculation(self):
        """Test duration calculation."""
        entry = SubtitleEntry(index=1, start_time=1000, end_time=5000)
        self.assertEqual(entry.duration, 4000)

    def test_time_formatting(self):
        """Test time formatting to SRT format."""
        entry = SubtitleEntry(index=1, start_time=0, end_time=0)

        # Test various times
        self.assertEqual(entry.format_time(0), "00:00:00,000")
        self.assertEqual(entry.format_time(1000), "00:00:01,000")
        self.assertEqual(entry.format_time(61000), "00:01:01,000")
        self.assertEqual(entry.format_time(3661000), "01:01:01,000")
        self.assertEqual(entry.format_time(1234567), "00:20:34,567")

    def test_time_properties(self):
        """Test start_time_str and end_time_str properties."""
        entry = SubtitleEntry(index=1, start_time=3661000, end_time=3662000)
        self.assertEqual(entry.start_time_str, "01:01:01,000")
        self.assertEqual(entry.end_time_str, "01:01:02,000")


class TestVobSubEntry(unittest.TestCase):
    """Test VobSubEntry class."""

    def test_entry_creation(self):
        """Test VobSubEntry creation."""
        entry = VobSubEntry(
            index=1,
            start_time=1000,
            end_time=5000,
            image_data=b'test_data',
            image_path='/path/to/image.sub',
            width=720,
            height=576
        )
        self.assertEqual(entry.index, 1)
        self.assertEqual(entry.start_time, 1000)
        self.assertEqual(entry.end_time, 5000)
        self.assertEqual(entry.image_data, b'test_data')
        self.assertEqual(entry.image_path, '/path/to/image.sub')
        self.assertEqual(entry.width, 720)
        self.assertEqual(entry.height, 576)

    def test_inheritance(self):
        """Test VobSubEntry inherits from SubtitleEntry."""
        entry = VobSubEntry(index=1, start_time=1000, end_time=5000)
        self.assertIsInstance(entry, SubtitleEntry)
        self.assertEqual(entry.duration, 4000)


class TestSRTEntry(unittest.TestCase):
    """Test SRTEntry class."""

    def test_entry_creation(self):
        """Test SRTEntry creation."""
        entry = SRTEntry(
            index=1,
            start_time=1000,
            end_time=5000,
            text="Hello World",
            editable=True
        )
        self.assertEqual(entry.index, 1)
        self.assertEqual(entry.text, "Hello World")
        self.assertTrue(entry.editable)

    def test_to_srt_format(self):
        """Test conversion to SRT format."""
        entry = SRTEntry(
            index=1,
            start_time=3661000,
            end_time=3662000,
            text="Hello World"
        )
        expected = "1\n01:01:01,000 --> 01:01:02,000\nHello World\n"
        self.assertEqual(entry.to_srt_format(), expected)

    def test_to_srt_format_multiline(self):
        """Test conversion with multiline text."""
        entry = SRTEntry(
            index=1,
            start_time=0,
            end_time=1000,
            text="Line 1\nLine 2"
        )
        expected = "1\n00:00:00,000 --> 00:00:01,000\nLine 1\nLine 2\n"
        self.assertEqual(entry.to_srt_format(), expected)

    def test_parse_time(self):
        """Test parsing SRT time format."""
        # Standard format
        self.assertEqual(SRTEntry.parse_time("00:00:01,000"), 1000)
        self.assertEqual(SRTEntry.parse_time("01:02:03,456"), 3723456)

        # With dot instead of comma
        self.assertEqual(SRTEntry.parse_time("00:00:01.000"), 1000)

        # With extra whitespace
        self.assertEqual(SRTEntry.parse_time(" 00:00:01,000 "), 1000)


class TestEntryComparison(unittest.TestCase):
    """Test comparison between entry types."""

    def test_time_comparison(self):
        """Test that entries can be compared by time."""
        vobsub = VobSubEntry(index=1, start_time=1000, end_time=4000)
        srt = SRTEntry(index=1, start_time=1100, end_time=4100, text="Test")

        time_diff = abs(vobsub.start_time - srt.start_time)
        self.assertEqual(time_diff, 100)


if __name__ == '__main__':
    unittest.main()
