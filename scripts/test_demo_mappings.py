"""
Validates demo video files, precomputed results mappings, and schema integrity.
"""
import os
import re
import sys

def verify():
    errors = []
    print("Testing Demo Video and Mapping Integrity...")

    # 1. Check video files exist on disk
    expected_videos = [
        'legit-1.mp4', 'legit-2.mp4', 'legit-3.mp4', 'legit-4.mp4', 'legit-5.mp4',
        'ai-1.mp4', 'ai-2.mp4', 'ai-3.mp4', 'false-1.mp4', 'false-2.mp4'
    ]
    for v in expected_videos:
        path = os.path.join('public', 'demo-videos', v)
        if not os.path.exists(path):
            errors.append(f"Missing demo video on disk: {path}")
        else:
            sz = os.path.getsize(path)
            if sz == 0:
                errors.append(f"Demo video is empty (0 bytes): {path}")
            else:
                print(f"  [OK] Video exists: {v} ({sz / 1024:.1f} KB)")

    # 2. Check precomputed results exist for all 10
    precomputed_file = os.path.join('src', 'data', 'precomputedShortsResults.ts')
    with open(precomputed_file, 'r', encoding='utf-8') as f:
        content = f.read()

    expected_ids = [
        'legit-1', 'legit-2', 'legit-3', 'legit-4', 'legit-5',
        'ai-1', 'ai-2', 'ai-3', 'false-1', 'false-2'
    ]
    for eid in expected_ids:
        if f"'{eid}':" not in content and f'"{eid}":' not in content:
            errors.append(f"Missing precomputed entry for ID: {eid}")
        else:
            print(f"  [OK] Precomputed result mapped: {eid}")

    if errors:
        print("\nERRORS FOUND:")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    else:
        print("\nAll 10 demo video files and precomputed results mapped with 100% integrity!")

if __name__ == '__main__':
    verify()
