from src.parser import ScreenplayParser

def test():
    ep1 = ScreenplayParser.parse_file('data/I Married a Broken Soldier. He was a Duke/episode-001-Episode 1671703.txt')
    print(f"Episode {ep1.episode_num}: Duration = {ep1.duration_str} ({ep1.duration_s}s)")
    print(f"Total Scenes: {len(ep1.scenes)}")
    print(f"Total Blocks: {len(ep1.all_blocks)}")
    dialogues = [b for b in ep1.all_blocks if b.block_type == 'DIALOGUE']
    print(f"Total Dialogues: {len(dialogues)}")
    print("First 5 dialogues:")
    for d in dialogues[:5]:
        print(f"  [{d.start_str} - {d.end_str}] {d.character} ({d.emotion}): {d.text}")

    print("\nLast 3 blocks of episode 1:")
    for b in ep1.all_blocks[-3:]:
        print(f"  [{b.start_str} - {b.end_str}] {b.block_type}: {b.text}")

if __name__ == '__main__':
    test()

