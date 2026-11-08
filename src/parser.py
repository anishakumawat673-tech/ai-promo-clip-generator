"""
Screenplay Parser for Kuku Microdrama Scripts.
Extracts structured scenes, actions, camera movements, dialogue, and timestamps.
"""

import os
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


def parse_timestamp(ts_str: str) -> float:
    """Converts MM:SS.ss or (MM:SS.ss) string into total seconds as float."""
    if not ts_str:
        return 0.0
    cleaned = ts_str.strip().replace("(", "").replace(")", "")
    match = re.search(r"(\d+):(\d+(?:\.\d+)?)", cleaned)
    if match:
        minutes = int(match.group(1))
        seconds = float(match.group(2))
        return round(minutes * 60 + seconds, 2)
    try:
        return round(float(cleaned), 2)
    except ValueError:
        return 0.0


def format_timestamp(seconds: float) -> str:
    """Converts total seconds into MM:SS.ss format."""
    if seconds < 0:
        seconds = 0.0
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes:02d}:{secs:05.2f}"


@dataclass
class ScriptBlock:
    block_type: str  # CAMERA, ACTION, SOUND FX, DIALOGUE
    start_s: float
    end_s: float
    text: str
    character: Optional[str] = None
    emotion: Optional[str] = None
    scene_num: int = 1
    episode_num: int = 1

    @property
    def duration_s(self) -> float:
        return max(0.0, round(self.end_s - self.start_s, 2))

    @property
    def start_str(self) -> str:
        return format_timestamp(self.start_s)

    @property
    def end_str(self) -> str:
        return format_timestamp(self.end_s)


@dataclass
class Scene:
    scene_num: int
    heading: str
    start_s: float
    end_s: float
    blocks: List[ScriptBlock] = field(default_factory=list)
    episode_num: int = 1

    @property
    def duration_s(self) -> float:
        return max(0.0, round(self.end_s - self.start_s, 2))


@dataclass
class Episode:
    episode_num: int
    raw_title: str
    logline: str
    continuity_notes: str
    scenes: List[Scene] = field(default_factory=list)
    file_path: str = ""

    @property
    def all_blocks(self) -> List[ScriptBlock]:
        blocks = []
        for scene in self.scenes:
            blocks.extend(scene.blocks)
        return blocks

    @property
    def duration_s(self) -> float:
        blocks = self.all_blocks
        if not blocks:
            return 0.0
        return max(b.end_s for b in blocks)

    @property
    def duration_str(self) -> str:
        return format_timestamp(self.duration_s)


class ScreenplayParser:
    """Parses microdrama screenplay text files into structured Episode objects."""

    HEADER_TAG_REGEX = re.compile(r"^\*\*(.+?)\*\*:?\s*$")
    TIMESTAMP_LINE_REGEX = re.compile(
        r"Start:\s*\(?([\d:\.]+)\)?\s*\|\s*End:\s*\(?([\d:\.]+)\)?"
    )

    @classmethod
    def parse_file(cls, file_path: str) -> Episode:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return cls.parse_text(content, file_path=file_path)

    @classmethod
    def parse_text(cls, text: str, file_path: str = "") -> Episode:
        lines = [line.strip() for line in text.splitlines()]

        episode_num = 1
        raw_title = os.path.basename(file_path) if file_path else "Episode"
        logline = ""
        continuity_notes = ""

        # Extract Episode Header Info
        for line in lines[:25]:
            if line.upper().startswith("EPISODE NUMBER:"):
                m = re.search(r"\d+", line)
                if m:
                    episode_num = int(m.group(0))
            elif line.upper().startswith("EPISODE LOGLINE:"):
                logline = line.split(":", 1)[1].strip()
            elif line.upper().startswith("CONTINUITY NOTES:"):
                continuity_notes = line.split(":", 1)[1].strip()

        # Split into Script content
        script_start_idx = 0
        for i, line in enumerate(lines):
            if "--- SCRIPT START ---" in line:
                script_start_idx = i + 1
                break

        script_lines = lines[script_start_idx:]
        scenes: List[Scene] = []
        current_scene: Optional[Scene] = None
        current_scene_num = 1

        i = 0
        while i < len(script_lines):
            line = script_lines[i]

            if not line or line.startswith("--- SCRIPT END ---"):
                i += 1
                continue

            # Check for SCENE Header
            scene_match = re.match(r"^SCENE\s+(\d+)", line, re.IGNORECASE)
            if scene_match:
                current_scene_num = int(scene_match.group(1))
                heading = ""
                s_start = 0.0
                s_end = 0.0
                i += 1
                while i < len(script_lines) and not script_lines[i].startswith("**"):
                    subline = script_lines[i]
                    if subline.lower().startswith("scene heading:"):
                        heading = subline.split(":", 1)[1].strip()
                    elif subline.lower().startswith("scene start:"):
                        s_start = parse_timestamp(subline.split(":", 1)[1].strip())
                    elif subline.lower().startswith("scene end:"):
                        s_end = parse_timestamp(subline.split(":", 1)[1].strip())
                    elif subline.lower().startswith("actions and dialogue:"):
                        pass
                    i += 1

                current_scene = Scene(
                    scene_num=current_scene_num,
                    heading=heading,
                    start_s=s_start,
                    end_s=s_end,
                    episode_num=episode_num,
                )
                scenes.append(current_scene)
                continue

            # Check for Block Header: **TAG:** or **TAG**:
            tag_match = cls.HEADER_TAG_REGEX.match(line)
            if tag_match:
                tag_content = tag_match.group(1).rstrip(":").strip()
                i += 1

                # Parse start / end timestamps
                start_s = 0.0
                end_s = 0.0
                if i < len(script_lines):
                    ts_match = cls.TIMESTAMP_LINE_REGEX.search(script_lines[i])
                    if ts_match:
                        start_s = parse_timestamp(ts_match.group(1))
                        end_s = parse_timestamp(ts_match.group(2))
                        i += 1

                # Collect subsequent descriptive/dialogue lines until next ** or SCENE
                text_lines = []
                while i < len(script_lines):
                    next_line = script_lines[i]
                    if (
                        cls.HEADER_TAG_REGEX.match(next_line)
                        or re.match(r"^SCENE\s+\d+", next_line, re.IGNORECASE)
                        or next_line.startswith("--- SCRIPT END ---")
                    ):
                        break
                    if next_line:
                        text_lines.append(next_line)
                    i += 1

                block_text = " ".join(text_lines).strip()

                # Determine block type and character info
                tag_upper = tag_content.upper()
                if tag_upper == "CAMERA":
                    b_type = "CAMERA"
                    char_name = None
                    emotion = None
                elif tag_upper == "ACTION":
                    b_type = "ACTION"
                    char_name = None
                    emotion = None
                elif tag_upper.startswith("SOUND"):
                    b_type = "SOUND FX"
                    char_name = None
                    emotion = None
                else:
                    # Character dialogue
                    b_type = "DIALOGUE"
                    # Check for emotion in parentheses e.g. "LADY JULIANA (Confused, Breathless)"
                    char_match = re.match(r"^([^\(]+)(?:\((.*)\))?$", tag_content)
                    if char_match:
                        char_name = char_match.group(1).strip()
                        emotion = (
                            char_match.group(2).strip() if char_match.group(2) else None
                        )
                    else:
                        char_name = tag_content
                        emotion = None

                block = ScriptBlock(
                    block_type=b_type,
                    start_s=start_s,
                    end_s=end_s,
                    text=block_text,
                    character=char_name,
                    emotion=emotion,
                    scene_num=current_scene_num,
                    episode_num=episode_num,
                )

                if current_scene is None:
                    current_scene = Scene(
                        scene_num=1,
                        heading="UNKNOWN",
                        start_s=start_s,
                        end_s=end_s,
                        episode_num=episode_num,
                    )
                    scenes.append(current_scene)

                current_scene.blocks.append(block)
                continue

            i += 1

        # If scene end wasn't set or is 0, estimate from last block
        for sc in scenes:
            if sc.blocks and (sc.end_s <= sc.start_s or sc.end_s == 0):
                sc.end_s = max(b.end_s for b in sc.blocks)
                sc.start_s = min(b.start_s for b in sc.blocks)

        return Episode(
            episode_num=episode_num,
            raw_title=raw_title,
            logline=logline,
            continuity_notes=continuity_notes,
            scenes=scenes,
            file_path=file_path,
        )

    @classmethod
    def parse_directory(cls, dir_path: str) -> List[Episode]:
        """Loads and parses all episode script files in directory, sorted by episode number."""
        episodes = []
        files = [
            os.path.join(dir_path, f)
            for f in os.listdir(dir_path)
            if f.endswith(".txt")
        ]
        for fpath in files:
            try:
                ep = cls.parse_file(fpath)
                episodes.append(ep)
            except Exception as e:
                print(f"Error parsing {fpath}: {e}")
        episodes.sort(key=lambda x: x.episode_num)
        return episodes
