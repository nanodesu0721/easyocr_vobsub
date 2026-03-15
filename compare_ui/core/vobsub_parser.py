"""VobSub (IDX/SUB) parser using BDSup2Sub for extraction."""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional, Tuple
from PIL import Image
import io
import subprocess
import os
import tempfile
import shutil

from .models import VobSubEntry


class VobSubParser:
    """Parser for VobSub subtitle files (IDX + SUB) using BDSup2Sub."""

    # Path to BDSup2Sub JAR file
    BDSUP2SUB_JAR = Path(__file__).parent.parent.parent / "BDSup2Sub.jar"

    def __init__(self):
        self.entries: List[VobSubEntry] = []
        self.idx_path: Optional[Path] = None
        self.sub_path: Optional[Path] = None
        self.xml_path: Optional[Path] = None
        self.image_dir: Optional[Path] = None
        self.palette: List[Tuple[int, int, int, int]] = []
        self.size: Tuple[int, int] = (720, 576)
        self._temp_dir: Optional[Path] = None

    def _get_cache_dir(self) -> Path:
        """Get cache directory for extracted files.

        Uses a persistent cache based on SUB file hash to avoid re-conversion.
        """
        if self.sub_path is None:
            raise RuntimeError("SUB path not set")

        # Create cache directory in user's temp folder
        cache_base = Path(tempfile.gettempdir()) / "easyocr_vobsub_cache"
        cache_base.mkdir(parents=True, exist_ok=True)

        # Use file hash (mtime + size) as cache key
        stat = self.sub_path.stat()
        cache_key = f"{self.sub_path.name}_{stat.st_mtime}_{stat.st_size}"
        cache_dir = cache_base / cache_key
        cache_dir.mkdir(parents=True, exist_ok=True)

        return cache_dir

    def parse(self, idx_path: str) -> List[VobSubEntry]:
        """Parse IDX file and associated SUB file using BDSup2Sub."""
        self.idx_path = Path(idx_path)
        self.sub_path = self.idx_path.with_suffix('.sub')

        if not self.sub_path.exists():
            raise FileNotFoundError(f"SUB file not found: {self.sub_path}")

        # Get cache directory for this SUB file
        cache_dir = self._get_cache_dir()
        self.xml_path = cache_dir / "subtitles.xml"
        self.image_dir = cache_dir

        # Convert using BDSup2Sub if XML doesn't exist
        if not self.xml_path.exists():
            self._convert_with_bdsup2sub(cache_dir)

        # Parse the XML file
        self._parse_xml()

        return self.entries

    def _convert_with_bdsup2sub(self, output_dir: Path):
        """Convert VobSub to XML+PNG using BDSup2Sub."""
        if not self.BDSUP2SUB_JAR.exists():
            raise FileNotFoundError(
                f"BDSup2Sub.jar not found at {self.BDSUP2SUB_JAR}. "
                "Please download it from https://github.com/mjuhasz/BDSup2Sub/wiki/Download"
            )

        # Create a temporary working directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Copy IDX and SUB files to temp directory
            temp_idx = temp_path / self.idx_path.name
            temp_sub = temp_path / self.sub_path.name
            shutil.copy2(str(self.idx_path), str(temp_idx))
            shutil.copy2(str(self.sub_path), str(temp_sub))

            # Run BDSup2Sub in temp directory
            temp_xml = temp_sub.with_suffix('.xml')
            cmd = [
                'java', '-jar', str(self.BDSUP2SUB_JAR),
                '-o', str(temp_xml),
                str(temp_sub)
            ]

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                # BDSup2Sub may output warnings but still succeed
                if result.returncode != 0 and not temp_xml.exists():
                    raise RuntimeError(f"BDSup2Sub failed: {result.stderr}")
            except subprocess.TimeoutExpired:
                raise RuntimeError("BDSup2Sub conversion timed out")
            except FileNotFoundError:
                raise RuntimeError("Java not found. Please install Java Runtime Environment.")

            # Copy generated files to cache directory
            if temp_xml.exists():
                # Copy XML
                shutil.copy2(str(temp_xml), str(self.xml_path))

                # Copy all PNG files
                # Use os.listdir instead of glob to avoid special character issues
                prefix = f"{temp_sub.stem}_"
                for filename in os.listdir(temp_path):
                    if filename.startswith(prefix) and filename.endswith('.png'):
                        png_file = temp_path / filename
                        dest = output_dir / filename
                        shutil.copy2(str(png_file), str(dest))

    def _parse_xml(self):
        """Parse BDSup2Sub-generated XML file."""
        if not self.xml_path.exists():
            raise FileNotFoundError(f"XML file not found: {self.xml_path}")

        tree = ET.parse(self.xml_path)
        root = tree.getroot()

        # Parse events
        events_elem = root.find('Events')
        if events_elem is None:
            raise ValueError("No Events element found in XML")

        self.entries = []
        for i, event in enumerate(events_elem.iter('Event'), 1):
            # Parse timecodes
            in_tc = event.get('InTC', '00:00:00:00')
            out_tc = event.get('OutTC', '00:00:00:00')

            start_time = self._parse_timecode(in_tc)
            end_time = self._parse_timecode(out_tc)

            # Parse graphic info
            graphic = event.find('Graphic')
            if graphic is not None:
                width = int(graphic.get('Width', 720))
                height = int(graphic.get('Height', 480))
                x_pos = int(graphic.get('X', 0))
                y_pos = int(graphic.get('Y', 0))
                image_file = graphic.text
            else:
                width = 720
                height = 480
                x_pos = 0
                y_pos = 0
                image_file = None

            entry = VobSubEntry(
                index=i,
                start_time=start_time,
                end_time=end_time,
                image_data=None,
                image_path=str(self.image_dir / image_file) if image_file else None,
                width=width,
                height=height
            )
            entry._x_pos = x_pos
            entry._y_pos = y_pos
            self.entries.append(entry)

    def _parse_timecode(self, tc: str) -> int:
        """Parse timecode string to milliseconds.

        Format: HH:MM:SS:FF (hours:minutes:seconds:frames)
        Assumes 25fps (PAL) based on BDSup2Sub output.
        """
        parts = tc.split(':')
        if len(parts) != 4:
            return 0

        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])
        frames = int(parts[3])

        # Convert to milliseconds (25fps)
        total_ms = hours * 3600000 + minutes * 60000 + seconds * 1000
        total_ms += int(frames * 1000 / 25)  # 25fps

        return total_ms

    def get_image(self, entry: VobSubEntry) -> Optional[Image.Image]:
        """Load subtitle image from PNG file."""
        if not entry.image_path:
            return None

        try:
            img = Image.open(entry.image_path)
            # Convert to RGBA if needed
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            return img
        except Exception as e:
            print(f"Error loading image for entry {entry.index}: {e}")
            return self._create_placeholder_image(entry)

    def _create_placeholder_image(self, entry: VobSubEntry) -> Image.Image:
        """Create a placeholder image when loading fails."""
        width = min(entry.width or 720, 720)
        height = min(entry.height or 480, 480)

        img = Image.new('RGBA', (width, height), (40, 40, 40, 255))

        try:
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            draw.rectangle([10, 10, width-10, height-10], outline=(80, 120, 180, 255), width=4)
            draw.text((width//2 - 60, height//2 - 80), f"#{entry.index}", fill=(255, 255, 255, 255))
            draw.text((width//2 - 100, height//2 + 20), "VobSub", fill=(180, 180, 180, 255))
        except Exception:
            pass

        return img

    def get_image_bytes(self, entry: VobSubEntry, format: str = 'PNG') -> Optional[bytes]:
        """Get image as bytes in specified format."""
        img = self.get_image(entry)
        if img:
            buffer = io.BytesIO()
            img.save(buffer, format=format)
            return buffer.getvalue()
        return None

    @staticmethod
    def clear_cache():
        """Clear all cached extracted files."""
        cache_base = Path(tempfile.gettempdir()) / "easyocr_vobsub_cache"
        if cache_base.exists():
            shutil.rmtree(cache_base)
