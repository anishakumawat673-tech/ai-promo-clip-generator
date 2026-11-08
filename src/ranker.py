"""
Global Promo Ranker and Acquisition Strategy Engine.
Ranks promos across all episodes, assigns marketing funnel tiers,
and exports clean JSON/CSV datasets for production teams.
"""

import os
import json
import csv
from typing import List, Dict, Any, Optional
from src.parser import Episode, ScreenplayParser
from src.candidate_gen import PromoCandidateGenerator, PromoCandidate
from src.evaluator import PromoEvaluator


class PromoRanker:
    """Ranks and stratifies promos across an entire microdrama series."""

    def __init__(self, evaluator: Optional[PromoEvaluator] = None):
        self.evaluator = evaluator or PromoEvaluator(provider="offline")
        self.candidate_gen = PromoCandidateGenerator()

    def process_series(self, episodes: List[Episode], top_k_per_episode: int = 3) -> List[Dict[str, Any]]:
        """Processes all episodes, scores candidate promos, and performs global ranking."""
        all_promos: List[Dict[str, Any]] = []

        for ep in episodes:
            candidates = self.candidate_gen.generate_candidates_for_episode(ep)
            top_candidates = candidates[:top_k_per_episode]

            for cand in top_candidates:
                eval_res = self.evaluator.evaluate_candidate(cand)
                
                promo_entry = {
                    "episode": ep.episode_num,
                    "episode_title": ep.raw_title,
                    "segments": [{
                        "segment_index": 1,
                        "episode": ep.episode_num,
                        "start_time": cand.start_str,
                        "end_time": cand.end_str,
                        "duration_s": cand.duration_s
                    }],
                    "total_duration_s": cand.duration_s,
                    "hook_first_3s": eval_res["hook_description"],
                    "cliffhanger_cut": eval_res["cliffhanger_description"],
                    "one_line_why_it_works": eval_res["why_it_works"],
                    "hook_score": eval_res["hook_score"],
                    "cliffhanger_score": eval_res["cliffhanger_score"],
                    "standalone_score": eval_res["standalone_score"],
                    "composite_score": eval_res["composite_score"],
                    "posting_priority": eval_res["posting_priority"],
                    "dialogue_preview": cand.get_dialogue_transcript(300)
                }
                all_promos.append(promo_entry)

        # Global cross-show ranking by composite score descending
        all_promos.sort(key=lambda p: p["composite_score"], reverse=True)

        # Assign global rank and strategic funnel tier
        for rank, p in enumerate(all_promos, start=1):
            p["global_rank"] = rank
            if rank <= 10:
                p["posting_strategy"] = "Tier 1: High-Velocity Cold Ads (Post First on TikTok/Shorts)"
            elif rank <= 30:
                p["posting_strategy"] = "Tier 2: Escalation & Retargeting Ads (Post Second for Binge Conversion)"
            else:
                p["posting_strategy"] = "Tier 3: Organic Episodic Promos (Niche / Lore Re-engagement)"

        return all_promos

    @staticmethod
    def export_to_json(promos: List[Dict[str, Any]], output_path: str):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(promos, f, indent=2, ensure_ascii=False)
        print(f"Exported {len(promos)} promos to {output_path}")

    @staticmethod
    def export_to_csv(promos: List[Dict[str, Any]], output_path: str):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        fieldnames = [
            "global_rank",
            "episode",
            "start_time",
            "end_time",
            "total_duration_s",
            "composite_score",
            "hook_score",
            "cliffhanger_score",
            "standalone_score",
            "posting_priority",
            "posting_strategy",
            "hook_first_3s",
            "cliffhanger_cut",
            "one_line_why_it_works",
            "dialogue_preview"
        ]

        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for p in promos:
                row = dict(p)
                row["start_time"] = p["segments"][0]["start_time"]
                row["end_time"] = p["segments"][0]["end_time"]
                writer.writerow(row)
        print(f"Exported {len(promos)} promos to {output_path}")

