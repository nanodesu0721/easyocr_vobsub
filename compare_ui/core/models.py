"""Data models for subtitle entries."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SubtitleEntry:
    """Base class for subtitle entries."""
    index: int
    start_time: int  # milliseconds
    end_time: int    # milliseconds

    @property
    def duration(self) -> int:
        """Calculate duration in milliseconds."""
        return self.end_time - self.start_time

    def format_time(self, ms: int) -> str:
        """Format milliseconds to SRT time format: HH:MM:SS,mmm"""
        hours = ms // 3600000
        ms %= 3600000
        minutes = ms // 60000
        ms %= 60000
        seconds = ms // 1000
        milliseconds = ms % 1000
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    @property
    def start_time_str(self) -> str:
        """Get start time as formatted string."""
        return self.format_time(self.start_time)

    @property
    def end_time_str(self) -> str:
        """Get end time as formatted string."""
        return self.format_time(self.end_time)


@dataclass
class VobSubEntry(SubtitleEntry):
    """VobSub subtitle entry with image data."""
    image_data: Optional[bytes] = None
    image_path: Optional[str] = None
    width: int = 0
    height: int = 0
    _cached_pixmap = None

    def __post_init__(self):
        self._cached_pixmap = None

    def invalidate_cache(self):
        """Clear cached pixmap to free memory."""
        self._cached_pixmap = None


@dataclass
class SRTEntry(SubtitleEntry):
    """SRT subtitle entry with text content."""
    text: str = ""
    editable: bool = True

    def to_srt_format(self) -> str:
        """Convert entry to SRT format string."""
        lines = [
            str(self.index),
            f"{self.start_time_str} --> {self.end_time_str}",
            self.text,
            ""  # Empty line between entries
        ]
        return "\n".join(lines)

    @staticmethod
    def parse_time(time_str: str) -> int:
        """Parse SRT time format to milliseconds."""
        # Format: HH:MM:SS,mmm or HH:MM:SS.mmm
        time_str = time_str.strip().replace('.', ',')
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds_parts = parts[2].split(',')
        seconds = int(seconds_parts[0])
        milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
        return hours * 3600000 + minutes * 60000 + seconds * 1000 + milliseconds
