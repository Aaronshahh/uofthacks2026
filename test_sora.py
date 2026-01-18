"""
Sora video generation - Text-to-Video only (no images)
Generates documentary scenes from the police report
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from scene_parser import SceneParser
from sora_service import SoraVideoService

load_dotenv()

REPORT_PATH = Path("footwear_rag/data/zip_files/message.txt")

print("=" * 70)
print("SORA TEXT-TO-VIDEO - Art Museum Documentary")
print("=" * 70)

if not os.getenv("OPENAI_API_KEY"):
    print("ERROR: OPENAI_API_KEY not set")
    exit(1)

if not REPORT_PATH.exists():
    print(f"ERROR: Report not found: {REPORT_PATH}")
    exit(1)

# Step 1: Parse report
print("\nStep 1: Parsing report into scenes...")
with open(REPORT_PATH, 'r', encoding='utf-8') as f:
    report_text = f.read()

parser = SceneParser()
parsed_scenes = parser.parse_report(report_text, num_images=3)

if "error" in parsed_scenes:
    print(f"ERROR: {parsed_scenes['error']}")
    exit(1)

print(f"Found {len(parsed_scenes.get('scenes', []))} scenes")

# Step 2: Generate prompts
print("\nStep 2: Generating documentary prompts...")
scene_prompts = parser.generate_video_prompts(parsed_scenes)

for p in scene_prompts:
    print(f"\n  Scene {p['scene_number']}:")
    print(f"    {p['prompt'][:120]}...")

# Step 3: Generate videos (TEXT ONLY - no images)
print("\n" + "=" * 70)
print("Step 3: Generating videos with Sora (TEXT-TO-VIDEO)")
print("=" * 70)
print("Each video takes 2-5 minutes...")

service = SoraVideoService()

results = {
    "completed": 0,
    "failed": 0,
    "videos": []
}

for scene in scene_prompts:
    scene_num = scene["scene_number"]
    prompt = scene["prompt"]
    
    print(f"\n{'─' * 60}")
    print(f"Generating Scene {scene_num}...")
    
    # Generate WITHOUT image
    result = service.generate_video(
        prompt=prompt,
        image_path=None,  # NO IMAGE - text only
        scene_number=scene_num,
        duration=5
    )
    
    results["videos"].append(result)
    
    if result["status"] == "complete":
        results["completed"] += 1
        print(f"  SUCCESS: {result.get('local_path')}")
    else:
        results["failed"] += 1
        print(f"  FAILED: {result.get('error', 'Unknown error')}")

# Summary
print("\n" + "=" * 70)
print("RESULTS")
print("=" * 70)
print(f"Completed: {results['completed']}/{len(scene_prompts)} scenes")

if results["videos"]:
    print("\nVideos:")
    for v in results["videos"]:
        status = v["status"]
        scene = v["scene_number"]
        if status == "complete":
            print(f"  Scene {scene}: {v.get('local_path')}")
        else:
            print(f"  Scene {scene}: {status} - {v.get('error', '')[:50]}")

if results["completed"] > 0:
    print(f"\nVideos saved to: outputs/videos/")

print("=" * 70)
