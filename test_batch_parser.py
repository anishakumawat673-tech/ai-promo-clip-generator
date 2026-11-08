from src.parser import ScreenplayParser
import time

def test_all():
    t0 = time.time()
    episodes = ScreenplayParser.parse_directory('data/I Married a Broken Soldier. He was a Duke')
    elapsed = time.time() - t0
    print(f"Successfully parsed {len(episodes)} episodes in {elapsed:.2f}s")
    total_blocks = sum(len(ep.all_blocks) for ep in episodes)
    total_scenes = sum(len(ep.scenes) for ep in episodes)
    total_duration = sum(ep.duration_s for ep in episodes)
    print(f"Total Scenes: {total_scenes}")
    print(f"Total Blocks: {total_blocks}")
    print(f"Total Runtime: {total_duration/60:.1f} minutes")
    print(f"Episode numbers: {[ep.episode_num for ep in episodes[:10]]} ... {[ep.episode_num for ep in episodes[-5:]]}")

if __name__ == '__main__':
    test_all()

