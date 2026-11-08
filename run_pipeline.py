"""
End-to-End Execution Pipeline for Kuku Promo Extraction.
Processes all 50 episodes, performs global ranking, executes quality audits,
and exports all required raw outputs.
"""

import time
import os
import json
from src.parser import ScreenplayParser
from src.ranker import PromoRanker
from src.evaluator import PromoEvaluator
from src.failure_analysis import PromoFailureAnalyzer


def main():
    print("=" * 70)
    print("🚀 KUKU MICRODRAMA PROMO EXTRACTION PIPELINE")
    print("=" * 70)

    data_dir = "data/I Married a Broken Soldier. He was a Duke"
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)

    t0 = time.time()

    # Step 1: Parse all screenplays
    print("\n[Step 1/5] Parsing screenplays across all episodes...")
    episodes = ScreenplayParser.parse_directory(data_dir)
    print(f"  ✓ Successfully parsed {len(episodes)} episodes.")

    # Step 2: Extract, score, and rank candidate promos
    print("\n[Step 2/5] Running candidate generation & multi-factor scoring...")
    evaluator = PromoEvaluator(provider="offline")
    ranker = PromoRanker(evaluator=evaluator)
    all_promos = ranker.process_series(episodes, top_k_per_episode=3)
    print(f"  ✓ Generated and scored {len(all_promos)} high-potential promos.")

    # Step 3: Run Quality Checking and Failure Audits
    print("\n[Step 3/5] Running quality checks & failure mode analysis...")
    audit_report = PromoFailureAnalyzer.generate_audit_report(all_promos)
    print(f"  ✓ Audited {audit_report['total_promos_audited']} promos.")
    print(f"  ✓ Clean Pass Rate: {audit_report['pass_rate_clean']}")
    print(f"  ✓ Flagged for Human-in-the-Loop review: {audit_report['flagged_for_human_review']}")

    # Step 4: Export Raw Outputs
    print("\n[Step 4/5] Exporting raw outputs for submission pack...")
    json_path = os.path.join(output_dir, "raw_promos_all_episodes.json")
    csv_path = os.path.join(output_dir, "raw_promos_all_episodes.csv")
    top_csv_path = os.path.join(output_dir, "top_ranked_promos.csv")
    audit_path = os.path.join(output_dir, "quality_audit_report.json")

    PromoRanker.export_to_json(all_promos, json_path)
    PromoRanker.export_to_csv(all_promos, csv_path)
    PromoRanker.export_to_csv(all_promos[:15], top_csv_path)

    with open(audit_path, "w", encoding="utf-8") as f:
        json.dump(audit_report, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Exported audit report to {audit_path}")

    elapsed = time.time() - t0
    print(f"\n[Step 5/5] Pipeline completed in {elapsed:.2f} seconds.")
    print("=" * 70)

    # Print Top 5 Promos
    print("\n🏆 TOP 5 PROMOS TO POST FIRST (Ranked by Conversion Potential):")
    for p in all_promos[:5]:
        print(f"\nRANK #{p['global_rank']} | Episode {p['episode']} | Range: {p['segments'][0]['start_time']} -> {p['segments'][0]['end_time']} ({p['total_duration_s']}s)")
        print(f"  Strategy:  {p['posting_strategy']}")
        print(f"  Scores:    Composite: {p['composite_score']} | Hook: {p['hook_score']} | Cliffhanger: {p['cliffhanger_score']} | Standalone: {p['standalone_score']}")
        print(f"  Hook (3s): {p['hook_first_3s'][:100]}")
        print(f"  Cliff Cut: {p['cliffhanger_cut'][:100]}")
        print(f"  Why it works: {p['one_line_why_it_works']}")


if __name__ == "__main__":
    main()

