"""Tests for VobSub parser."""

import unittest
import tempfile
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.vobsub_parser import VobSubParser
from core.models import VobSubEntry


class TestVobSubParser(unittest.TestCase):
    """Test VobSubParser class."""

    def setUp(self):
        """Set up test fixtures."""
        self.parser = VobSubParser()

    def create_test_idx_file(self, content):
        """Helper to create a test IDX file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.idx', delete=False, encoding='utf-8') as f:
            f.write(content)
            return f.name

    def create_test_sub_file(self, idx_path, data=b''):
        """Helper to create a test SUB file."""
        sub_path = idx_path.replace('.idx', '.sub')
        with open(sub_path, 'wb') as f:
            f.write(data)
        return sub_path

    def test_parse_idx_basic(self):
        """Test parsing a basic IDX file."""
        idx_content = """# VobSub index file, v7
size: 720x576
palette: 000000, 0000ff, 00ff00, ff0000, ffff00, ff00ff, 00ffff, ffffff, 808080, 8080ff, 80ff80, ff8080, ffff80, ff80ff, 80ffff, c0c0c0
timestamp: 00:00:01:000, filepos: 000000000
timestamp: 00:00:05:000, filepos: 000001000
timestamp: 00:00:10:000, filepos: 000002000
"""
        idx_path = self.create_test_idx_file(idx_content)
        sub_path = self.create_test_sub_file(idx_path, b'\x00' * 3000)

        try:
            entries = self.parser.parse(idx_path)
            self.assertEqual(len(entries), 3)

            # Check first entry
            self.assertEqual(entries[0].index, 1)
            self.assertEqual(entries[0].start_time, 1000)  # 00:00:01:000
            self.assertEqual(entries[0].width, 720)
            self.assertEqual(entries[0].height, 576)

            # Check second entry
            self.assertEqual(entries[1].index, 2)
            self.assertEqual(entries[1].start_time, 5000)  # 00:00:05:000
        finally:
            os.unlink(idx_path)
            if os.path.exists(sub_path):
                os.unlink(sub_path)

    def test_parse_idx_with_size(self):
        """Test parsing IDX with custom size."""
        idx_content = """# VobSub index file, v7
size: 1920x1080
palette: 000000, 0000ff, 00ff00, ff0000, ffff00, ff00ff, 00ffff, ffffff, 808080, 8080ff, 80ff80, ff8080, ffff80, ff80ff, 80ffff, c0c0c0
timestamp: 00:01:00:000, filepos: 000000000
"""
        idx_path = self.create_test_idx_file(idx_content)
        sub_path = self.create_test_sub_file(idx_path, b'\x00' * 1000)

        try:
            entries = self.parser.parse(idx_path)
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].width, 1920)
            self.assertEqual(entries[0].height, 1080)
            self.assertEqual(entries[0].start_time, 60000)  # 00:01:00:000
        finally:
            os.unlink(idx_path)
            if os.path.exists(sub_path):
                os.unlink(sub_path)

    def test_end_time_calculation(self):
        """Test that end times are calculated correctly."""
        idx_content = """# VobSub index file, v7
size: 720x576
palette: 000000, 0000ff, 00ff00, ff0000, ffff00, ff00ff, 00ffff, ffffff, 808080, 8080ff, 80ff80, ff8080, ffff80, ff80ff, 80ffff, c0c0c0
timestamp: 00:00:01:000, filepos: 000000000
timestamp: 00:00:05:000, filepos: 000001000
timestamp: 00:00:10:000, filepos: 000002000
"""
        idx_path = self.create_test_idx_file(idx_content)
        sub_path = self.create_test_sub_file(idx_path, b'\x00' * 3000)

        try:
            entries = self.parser.parse(idx_path)

            # First entry should end when second starts
            self.assertEqual(entries[0].end_time, entries[1].start_time)
            # Second entry should end when third starts
            self.assertEqual(entries[1].end_time, entries[2].start_time)
            # Last entry should have a default duration
            self.assertEqual(entries[2].end_time, entries[2].start_time + 3000)
        finally:
            os.unlink(idx_path)
            if os.path.exists(sub_path):
                os.unlink(sub_path)

    def test_missing_sub_file(self):
        """Test that missing SUB file raises error."""
        idx_content = """# VobSub index file, v7
timestamp: 00:00:01:000, filepos: 000000000
"""
        idx_path = self.create_test_idx_file(idx_content)

        try:
            with self.assertRaises(FileNotFoundError):
                self.parser.parse(idx_path)
        finally:
            os.unlink(idx_path)

    def test_palette_parsing(self):
        """Test palette parsing from IDX."""
        # Note: Palette values are in ARGB format (8 hex digits)
        idx_content = """# VobSub index file, v7
size: 720x576
palette: ff000000, ff0000ff, ff00ff00, ffff0000, ffffff00, ffff00ff, ff00ffff, ffffffff, ff808080, ff8080ff, ff80ff80, ffff8080, ffffff80, ffff80ff, ff80ffff, ffc0c0c0
timestamp: 00:00:01:000, filepos: 000000000
"""
        idx_path = self.create_test_idx_file(idx_content)
        sub_path = self.create_test_sub_file(idx_path, b'\x00' * 1000)

        try:
            entries = self.parser.parse(idx_path)
            self.assertEqual(len(self.parser.palette), 16)
            # Check first color (black with full alpha)
            self.assertEqual(self.parser.palette[0], (0, 0, 0, 255))
            # Check blue color (full alpha, blue channel)
            self.assertEqual(self.parser.palette[1], (0, 0, 255, 255))
            # Check green color
            self.assertEqual(self.parser.palette[2], (0, 255, 0, 255))
        finally:
            os.unlink(idx_path)
            if os.path.exists(sub_path):
                os.unlink(sub_path)


class TestVobSubEntry(unittest.TestCase):
    """Test VobSubEntry data model."""

    def test_entry_with_image_data(self):
        """Test VobSubEntry with image data."""
        entry = VobSubEntry(
            index=1,
            start_time=1000,
            end_time=4000,
            image_data=b'test_image_bytes',
            image_path='/test/path.sub',
            width=720,
            height=576
        )
        self.assertEqual(entry.image_data, b'test_image_bytes')
        self.assertEqual(entry.image_path, '/test/path.sub')


if __name__ == '__main__':
    unittest.main()
