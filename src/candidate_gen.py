"""
Candidate Generator for Microdrama Promos.
Extracts 20-60 second candidate segments from screenplay episodes,
evaluates heuristic quality, and deduplicates overlapping windows using Non-Maximum Suppression (NMS).
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from src.parser import Episode, ScriptBlock, format_timestamp
from src.heuristics import ScreenplayHeuristics


@dataclass
class PromoCandidate:
    episode_num: int
    start_s: float
    end_s: float
    blocks: List[ScriptBlock] = field(default_factory=list)
    
    # Feature scores
    hook_score: float = 0.0
    cliffhanger_score: float = 0.0
    standalone_score: float = 0.0
    composite_score: float = 0.0
    
    # Qualitative descriptions
    hook_text: str = ""
    cliffhanger_text: str = ""
    standalone_text: str = ""
    why_it_works: str = ""
    funnel_category: str = "Top-of-Funnel (Cold Audience)"
    
    # Optional multi-segment support
    segments: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def duration_s(self) -> float:
        return round(self.end_s - self.start_s, 2)

    @property
    def start_str(self) -> str:
        return format_timestamp(self.start_s)

    @property
    def end_str(self) -> str:
        return format_timestamp(self.end_s)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "episode_num": self.episode_num,
            "start_time": self.start_str,
            "end_time": self.end_str,
            "duration_s": self.duration_s,
            "composite_score": round(self.composite_score, 2),
            "hook_score": self.hook_score,
            "cliffhanger_score": self.cliffhanger_score,
            "standalone_score": self.standalone_score,
            "hook_summary": self.hook_text,
            "cliffhanger_summary": self.cliffhanger_text,
            "why_it_works": self.why_it_works,
            "funnel_category": self.funnel_category,
            "dialogue_excerpt": self.get_dialogue_transcript()
        }

    def get_dialogue_transcript(self, max_chars: int = 400) -> str:
        dialogues = [b for b in self.blocks if b.block_type == "DIALOGUE"]
        lines = []
        for d in dialogues:
            lines.append(f"{d.character or 'Character'}: \"{d.text}\"")
        transcript = " | ".join(lines)
        if len(transcript) > max_chars:
            transcript = transcript[:max_chars] + "..."
        return transcript


class PromoCandidateGenerator:
    """Generates and ranks valid 20-60 second promo segments for an episode."""

    def __init__(
        self,
        min_duration_s: float = 20.0,
        max_duration_s: float = 60.0,
        hook_window_s: float = 3.5,
        cliff_window_s: float = 4.5,
        iou_overlap_threshold: float = 0.50
    ):
        self.min_duration_s = min_duration_s
        self.max_duration_s = max_duration_s
        self.hook_window_s = hook_window_s
        self.cliff_window_s = cliff_window_s
        self.iou_overlap_threshold = iou_overlap_threshold

    def generate_candidates_for_episode(self, episode: Episode) -> List[PromoCandidate]:
        blocks = episode.all_blocks
        if not blocks:
            return []

        raw_candidates: List[PromoCandidate] = []
        n_blocks = len(blocks)

        for i in range(n_blocks):
            start_block = blocks[i]
            # Must start on dialogue, sound, or action (skip purely camera establishing shots if possible)
            start_time = start_block.start_s

            for j in range(i, n_blocks):
                end_block = blocks[j]
                end_time = end_block.end_s
                duration = end_time - start_time

                if duration < self.min_duration_s:
                    continue
                if duration > self.max_duration_s:
                    break

                # Segment slice
                segment_blocks = blocks[i : j + 1]

                # Identify hook blocks (first 3.5s)
                hook_blocks = [b for b in segment_blocks if b.start_s <= start_time + self.hook_window_s]
                # Identify cliffhanger blocks (last 4.5s)
                cliff_blocks = [b for b in segment_blocks if b.end_s >= end_time - self.cliff_window_s]

                hook_res = ScreenplayHeuristics.evaluate_hook(hook_blocks)
                cliff_res = ScreenplayHeuristics.evaluate_cliffhanger(cliff_blocks)
                stand_res = ScreenplayHeuristics.evaluate_standalone(segment_blocks)

                # Composite score weighting: 40% Hook, 35% Cliffhanger, 25% Standalone
                composite = (
                    0.40 * hook_res["score"] +
                    0.35 * cliff_res["score"] +
                    0.25 * stand_res["score"]
                )

                # Generate concise "why it works" pitch
                why_reasons = []
                if hook_res["reasons"]:
                    why_reasons.append(hook_res["reasons"][0])
                if cliff_res["reasons"]:
                    why_reasons.append(cliff_res["reasons"][0])
                why_pitch = " + ".join(why_reasons) if why_reasons else "Balanced narrative beat with natural tension."

                # Funnel categorisation
                if hook_res["score"] >= 7.5 and stand_res["score"] >= 6.5:
                    funnel = "Top-of-Funnel (Cold Audience - High Shock)"
                elif cliff_res["score"] >= 7.5:
                    funnel = "Mid-Funnel (Binge Hook - High Cliffhanger)"
                else:
                    funnel = "Secondary Promo (Character / Lore Focus)"

                candidate = PromoCandidate(
                    episode_num=episode.episode_num,
                    start_s=start_time,
                    end_s=end_time,
                    blocks=segment_blocks,
                    hook_score=hook_res["score"],
                    cliffhanger_score=cliff_res["score"],
                    standalone_score=stand_res["score"],
                    composite_score=round(composite, 2),
                    hook_text=hook_res["text"],
                    cliffhanger_text=cliff_res["text"],
                    standalone_text=stand_res["text"],
                    why_it_works=why_pitch,
                    funnel_category=funnel,
                    segments=[{
                        "segment_index": 1,
                        "episode": episode.episode_num,
                        "start_time": format_timestamp(start_time),
                        "end_time": format_timestamp(end_time),
                        "duration_s": round(duration, 2)
                    }]
                )
                raw_candidates.append(candidate)

        # Deduplicate overlapping clips using Non-Maximum Suppression (NMS)
        return self._apply_nms(raw_candidates)

    def _apply_nms(self, candidates: List[PromoCandidate]) -> List[PromoCandidate]:
        """Suppresses heavily overlapping candidate clips, keeping the highest-scoring ones."""
        if not candidates:
            return []

        # Sort by composite score descending
        candidates.sort(key=lambda c: c.composite_score, reverse=True)
        selected: List[PromoCandidate] = []

        for cand in candidates:
            overlap = False
            for kept in selected:
                # Calculate Intersection over Union (IoU) of time ranges
                inter_start = max(cand.start_s, kept.start_s)
                inter_end = min(cand.end_s, kept.end_s)
                inter_dur = max(0.0, inter_end - inter_start)

                union_start = min(cand.start_s, kept.start_s)
                union_end = max(cand.end_s, kept.end_s)
                union_dur = union_end - union_start

                iou = inter_dur / union_dur if union_dur > 0 else 0.0

                if iou >= self.iou_overlap_threshold:
                    overlap = True
                    break

            if not overlap:
                selected.append(cand)

        return selected

