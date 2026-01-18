"""
Test 100% FREE image-to-video with Hugging Face Spaces
NO API key, NO signup, NO costs!
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from scene_parser import SceneParser
from space_video_service import SpaceVideoService

# Load environment variables
load_dotenv()

# Configuration
REPORT_PATH = Path("footwear_rag/data/zip_files/message.txt")
IMAGE_PATHS = [
    Path("footwear_rag/data/zip_files/begining_heist.png"),
    Path("footwear_rag/data/zip_files/middle_heist.png"),
    Path("footwear_rag/data/zip_files/leaving_heist.png")
]

print("="*70)
print("100% FREE VIDEO TEST - Isabella Stewart Gardner Museum Heist")
print("Using Hugging Face Spaces - NO API key needed!")
print("="*70)

# Check OPENAI_API_KEY for scene parser
if not os.getenv("OPENAI_API_KEY"):
    print("\nNOTE: OPENAI_API_KEY not set")
    print("Scene parser needs this (costs ~$0.0001 per report)")
    print("Or you can skip parsing and test video generation only")
    print("\nFor now, skipping scene parsing...")
    
    # Test with a simple scene
    scene_prompts = [{
        "scene_number": 1,
        "prompt": "Art museum investigation documentary. Elegant museum gallery. Professional mysterious cinematography.",
        "image_index": 0
    }]
    parsed_scenes = None
else:
    # Check files
    print(f"\nReport: {'Found' if REPORT_PATH.exists() else 'NOT FOUND'} - {REPORT_PATH}")
    for img in IMAGE_PATHS:
        print(f"Image:  {'Found' if img.exists() else 'NOT FOUND'} - {img.name}")

    if not REPORT_PATH.exists() or not all(img.exists() for img in IMAGE_PATHS):
        print("\nERROR: Some files not found!")
        exit(1)

    # Parse report
    print("\n" + "="*70)
    print("STEP 1: Parse Police Report")
    print("="*70)

    with open(REPORT_PATH, 'r', encoding='utf-8') as f:
        report_text = f.read()

    parser = SceneParser()
    parsed_scenes = parser.parse_report(report_text, num_images=len(IMAGE_PATHS))

    if "error" in parsed_scenes:
        print(f"ERROR: {parsed_scenes['error']}")
        exit(1)

    print(f"\nParsed {len(parsed_scenes['scenes'])} scenes")
    for scene in parsed_scenes['scenes']:
        print(f"  {scene['scene_number']}. {scene['location']} @ {scene['timestamp']}")

    # Generate video prompts
    scene_prompts = parser.generate_video_prompts(parsed_scenes)

print("\n" + "="*70)
print("STEP 2: Generate FREE Videos with Hugging Face Spaces")
print("="*70)
print("Using CogVideoX-5B Space - completely free!")
print("Each video takes 2-5 minutes")
print("NO API key needed. NO signup. NO costs!")
print("="*70)

# Initialize service
service = SpaceVideoService()

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
print(f"Cost: $0.00 (100% FREE!)")

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
    print(f"\nSuccess! Check outputs/videos/ for your FREE videos!")
else:
    print(f"\nNo videos generated. Check errors above.")
    print("Note: Spaces can be busy. Try again in a few minutes!")
