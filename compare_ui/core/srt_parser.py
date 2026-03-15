"""SRT subtitle parser with encoding detection."""

import re
import chardet
from pathlib import Path
from typing import List, Optional

from .models import SRTEntry


class SRTParser:
    """Parser for SRT subtitle files with automatic encoding detection."""

    def __init__(self):
        self.entries: List[SRTEntry] = []
        self.file_path: Optional[Path] = None
        self.encoding: str = 'utf-8'

    def parse(self, file_path: str) -> List[SRTEntry]:
        """Parse SRT file with automatic encoding detection."""
        self.file_path = Path(file_path)

        # Detect encoding
        self.encoding = self._detect_encoding()

        # Read content
        with open(self.file_path, 'r', encoding=self.encoding, errors='replace') as f:
            content = f.read()

        self.entries = self._parse_content(content)
        return self.entries

    def _detect_encoding(self) -> str:
        """Detect file encoding using chardet."""
        with open(self.file_path, 'rb') as f:
            raw_data = f.read()

        result = chardet.detect(raw_data)
        detected = result.get('encoding', 'utf-8')

        # Map common encodings
        encoding_map = {
            'GB2312': 'gbk',
            'GBK': 'gbk',
            'GB18030': 'gb18030',
            'BIG5': 'big5',
            'ASCII': 'utf-8',
            'UTF-8-SIG': 'utf-8',
        }

        return encoding_map.get(detected.upper(), detected or 'utf-8')

    def _parse_content(self, content: str) -> List[SRTEntry]:
        """Parse SRT content into entries."""
        entries = []

        # Normalize line endings
        content = content.replace('\r\n', '\n').replace('\r', '\n')

        # Split into blocks (separated by blank lines)
        blocks = re.split(r'\n\s*\n', content.strip())

        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 2:
                continue

            # First line should be index number
            try:
                index = int(lines[0].strip())
            except ValueError:
                continue

            # Second line should be time range
            time_line = lines[1].strip()
            time_match = re.match(
                r'(\d{1,2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}[,.]\d{3})',
                time_line
            )

            if not time_match:
                continue

            start_time = SRTEntry.parse_time(time_match.group(1))
            end_time = SRTEntry.parse_time(time_match.group(2))

            # Remaining lines are subtitle text
            text = '\n'.join(lines[2:]).strip()

            entry = SRTEntry(
                index=index,
                start_time=start_time,
                end_time=end_time,
                text=text,
                editable=True
            )
            entries.append(entry)

        return entries

    def save(self, file_path: Optional[str] = None, encoding: str = 'utf-8') -> bool:
        """Save entries to SRT file."""
        save_path = Path(file_path) if file_path else self.file_path
        if not save_path:
            return False

        try:
            with open(save_path, 'w', encoding=encoding) as f:
                for i, entry in enumerate(self.entries, 1):
                    entry.index = i  # Reindex
                    f.write(entry.to_srt_format())
                    f.write('\n')
            return True
        except Exception as e:
            print(f"Error saving SRT: {e}")
            return False

    def add_entry(self, index: int, start_time: int, end_time: int, text: str = "") -> SRTEntry:
        """Add a new entry at specified index."""
        entry = SRTEntry(
            index=index,
            start_time=start_time,
            end_time=end_time,
            text=text,
            editable=True
        )
        self.entries.insert(index - 1, entry)
        self._reindex()
        return entry

    def delete_entry(self, index: int) -> bool:
        """Delete entry at specified index."""
        for i, entry in enumerate(self.entries):
            if entry.index == index:
                del self.entries[i]
                self._reindex()
                return True
        return False

    def duplicate_entry(self, index: int) -> Optional[SRTEntry]:
        """Duplicate entry at specified index."""
        for i, entry in enumerate(self.entries):
            if entry.index == index:
                new_entry = SRTEntry(
                    index=index + 1,
                    start_time=entry.start_time,
                    end_time=entry.end_time,
                    text=entry.text,
                    editable=True
                )
                self.entries.insert(i + 1, new_entry)
                self._reindex()
                return new_entry
        return None

    def _reindex(self):
        """Reindex all entries."""
        for i, entry in enumerate(self.entries, 1):
            entry.index = i

    def get_entry(self, index: int) -> Optional[SRTEntry]:
        """Get entry by index."""
        for entry in self.entries:
            if entry.index == index:
                return entry
        return None
