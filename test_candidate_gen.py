from src.parser import ScreenplayParser
from src.candidate_gen import PromoCandidateGenerator

def test_gen():
    ep1 = ScreenplayParser.parse_file('data/I Married a Broken Soldier. He was a Duke/episode-001-Episode 1671703.txt')
    generator = PromoCandidateGenerator()
    candidates = generator.generate_candidates_for_episode(ep1)

    print(f"Generated {len(candidates)} non-overlapping promos for Episode 1:")
    for idx, c in enumerate(candidates[:5]):
        print(f"\n--- Promo #{idx+1} [Score: {c.composite_score:.2f}] ---")
        print(f"Timestamp: {c.start_str} -> {c.end_str} (Duration: {c.duration_s}s)")
        print(f"Category:  {c.funnel_category}")
        print(f"Hook (first 3s) [{c.hook_score}/10]: {c.hook_text}")
        print(f"Cliffhanger [{c.cliffhanger_score}/10]: {c.cliffhanger_text}")
        print(f"Standalone [{c.standalone_score}/10]: {c.standalone_text}")
        print(f"Why it works: {c.why_it_works}")
        print(f"Dialogue snippet: {c.get_dialogue_transcript(150)}")

if __name__ == '__main__':
    test_gen()

