"""
CLI Tool to Test Promo Extraction on a Single Episode or Custom Screenplay.
Usage:
    python test_one.py              # Tests Episode 1 by default
    python test_one.py 5            # Tests Episode 5
    python test_one.py path/to/script.txt  # Tests any custom screenplay file
"""

import sys
import os
import glob
from src.parser import ScreenplayParser
from src.candidate_gen import PromoCandidateGenerator
from src.evaluator import PromoEvaluator


def find_episode_file(target: str) -> str:
    """Finds the screenplay file corresponding to an episode number or path."""
    if os.path.isfile(target):
        return target
    
    data_dir = os.path.join("data", "I Married a Broken Soldier. He was a Duke")
    if not os.path.exists(data_dir):
        # Check subdirectories of data
        matches = glob.glob("data/*/*.txt")
        if matches:
            data_dir = os.path.dirname(matches[0])

    if target.isdigit():
        ep_num = int(target)
        candidates = glob.glob(f"{data_dir}/episode-{ep_num:03d}*.txt")
        if candidates:
            return candidates[0]
        # Try generic search
        for f in glob.glob(f"{data_dir}/*.txt"):
            if f"episode-{ep_num:03d}" in f.lower() or f"episode {ep_num}" in f.lower():
                return f

    return target


def test_single_episode(target: str = "1"):
    file_path = find_episode_file(target)

    if not os.path.exists(file_path):
        print(f"❌ Error: Screenplay file not found for target '{target}'.")
        print(f"   Looked at: {file_path}")
        return

    print("=" * 75)
    print(f"🎬 KUKU PROMO EXTRACTION — SINGLE EPISODE TEST")
    print(f"   Target: {os.path.basename(file_path)}")
    print("=" * 75)

    # 1. Parse Episode
    print("\n[1/3] Parsing screenplay text and timestamps...")
    episode = ScreenplayParser.parse_file(file_path)
    print(f"  ✓ Episode Number: {episode.episode_num}")
    print(f"  ✓ Total Runtime:  {episode.duration_str} ({episode.duration_s} seconds)")
    print(f"  ✓ Total Scenes:   {len(episode.scenes)}")
    print(f"  ✓ Total Blocks:   {len(episode.all_blocks)}")
    if episode.logline:
        print(f"  ✓ Logline:        {episode.logline[:100]}...")

    # 2. Extract Candidate Promos
    print("\n[2/3] Generating candidate clips (20s - 60s windows)...")
    generator = PromoCandidateGenerator(
        min_duration_s=20.0,
        max_duration_s=60.0,
        hook_window_s=3.5,
        cliff_window_s=4.5
    )
    candidates = generator.generate_candidates_for_episode(episode)
    print(f"  ✓ Extracted {len(candidates)} non-overlapping candidate promos.")

    # 3. Score & Evaluate Promos
    print("\n[3/3] Scoring Promos against Hook, Cliffhanger & Standalone criteria...")
    evaluator = PromoEvaluator(provider="offline")

    top_candidates = candidates[:3]
    for idx, cand in enumerate(top_candidates, start=1):
        eval_res = evaluator.evaluate_candidate(cand)
        print("\n" + "-" * 75)
        print(f"🏆 TOP PROMO #{idx} | Timestamps: [{cand.start_str}  -->  {cand.end_str}] ({cand.duration_s}s)")
        print(f"   Strategy Tier: {eval_res['posting_priority']}")
        print(f"   Scores:        Composite: {eval_res['composite_score']}/10  |  Hook: {eval_res['hook_score']}/10  |  Cliffhanger: {eval_res['cliffhanger_score']}/10  |  Standalone: {eval_res['standalone_score']}/10")
        print(f"\n   🎣 First 3 Seconds (Hook):")
        print(f"      \"{eval_res['hook_description']}\"")
        print(f"\n   ⚡ Final Seconds (Cliffhanger Cut):")
        print(f"      \"{eval_res['cliffhanger_description']}\"")
        print(f"\n   💡 Why It Converts Scrolling Viewers:")
        print(f"      {eval_res['why_it_works']}")
        print(f"\n   📜 Dialogue Transcript:")
        dialogues = [b for b in cand.blocks if b.block_type == "DIALOGUE"]
        for d in dialogues[:5]:
            print(f"      [{d.start_str}] {d.character or 'Character'}: \"{d.text}\"")
        if len(dialogues) > 5:
            print(f"      ... (+{len(dialogues) - 5} more dialogue turns)")

    print("\n" + "=" * 75)
    print("✅ Single episode test complete!")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "1"
    test_single_episode(arg)

