"""
Test Replicate image-to-video with all heist images
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from scene_parser import SceneParser
from replicate_video_service import ReplicateVideoService

# Load environment
load_dotenv()

# Configuration
REPORT_PATH = Path("footwear_rag/data/zip_files/message.txt")
IMAGE_PATHS = [
    Path("footwear_rag/data/zip_files/begining_heist.png"),
    Path("footwear_rag/data/zip_files/middle_heist.png"),
    Path("footwear_rag/data/zip_files/leaving_heist.png")
]

print("="*70)
print("REPLICATE VIDEO TEST - Isabella Stewart Gardner Museum Heist")
print("="*70)

# Check API tokens
if not os.getenv("REPLICATE_API_TOKEN"):
    print("\nERROR: REPLICATE_API_TOKEN not set in .env")
    print("Get it from: https://replicate.com/account/api-tokens")
    exit(1)

if not os.getenv("OPENAI_API_KEY"):
    print("\nERROR: OPENAI_API_KEY not set in .env")
    exit(1)

print(f"\nReplicate Token: Set")
print(f"OpenAI Token: Set")

# Check files
print(f"\nReport: {'Found' if REPORT_PATH.exists() else 'NOT FOUND'} - {REPORT_PATH}")
for img in IMAGE_PATHS:
    print(f"Image:  {'Found' if img.exists() else 'NOT FOUND'} - {img.name}")

if not REPORT_PATH.exists() or not all(img.exists() for img in IMAGE_PATHS):
    print("\nERROR: Some files not found!")
    exit(1)

# Parse report
print("\n" + "="*70)
print("STEP 1: Parse Police Report into Scenes")
print("="*70)

with open(REPORT_PATH, 'r', encoding='utf-8') as f:
    report_text = f.read()

parser = SceneParser()
parsed_scenes = parser.parse_report(report_text, num_images=len(IMAGE_PATHS))

if "error" in parsed_scenes:
    print(f"ERROR: Scene parsing failed - {parsed_scenes['error']}")
    exit(1)

print(f"\nParsed {len(parsed_scenes['scenes'])} scenes:")
for scene in parsed_scenes['scenes']:
    print(f"  Scene {scene['scene_number']}: {scene['location']} @ {scene['timestamp']}")
    print(f"    Mood: {scene['mood']}")
    print(f"    Image: {scene.get('associated_image_index', 'None')}")

# Generate video prompts
scene_prompts = parser.generate_video_prompts(parsed_scenes)

print("\n" + "="*70)
print("STEP 2: Generate Videos with Replicate")
print("="*70)
print(f"Cost: ~${len(scene_prompts) * 0.03:.2f} from your FREE $10 credit")
print("Each video takes 2-5 minutes")
print("="*70)

# Initialize service
service = ReplicateVideoService()

# Generate videos
result = service.generate_reconstruction(
    scene_prompts=scene_prompts,
    image_paths=[str(p) for p in IMAGE_PATHS]
)

# Display results
print("\n" + "="*70)
print("RESULTS")
print("="*70)
print(f"Status: {result['status']}")
print(f"Completed: {result['completed']}/{result['total_scenes']} scenes")
print(f"Cost: ~${result['completed'] * 0.03:.2f} from FREE $10 credit")

if result['videos']:
    print("\nGenerated Videos:")
    for video in result['videos']:
        scene_num = video['scene_number']
        status = video['status']
        print(f"\n  Scene {scene_num}: {status}")
        if status == "complete":
            print(f"    File: {video.get('local_path')}")
            print(f"    Model: {video.get('model')}")
            print(f"    Cost: {video.get('cost')}")
        elif 'error' in video:
            print(f"    Error: {video['error']}")

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)

if result['completed'] > 0:
    print(f"\nSuccess! Videos saved to outputs/videos/")
    print(f"Remaining credit: ~${10 - (result['completed'] * 0.03):.2f}")
else:
    print(f"\nNo videos generated. Check errors above.")