"""
Test FREE image-to-video generation with heist images
Uses Hugging Face Inference API - 100% FREE, no costs!
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from scene_parser import SceneParser
from huggingface_video_service import HuggingFaceVideoService

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
print("FREE IMAGE-TO-VIDEO TEST - Isabella Stewart Gardner Museum Heist")
print("Using Hugging Face Inference API - 100% FREE!")
print("="*70)

# Check API token
if not os.getenv("HUGGINGFACE_TOKEN"):
    print("\nSETUP REQUIRED: HUGGINGFACE_TOKEN not set")
    print("\nTo get your FREE token (takes 1 minute):")
    print("1. Go to: https://huggingface.co/settings/tokens")
    print("2. Click 'New token'")
    print("3. Give it a name (e.g., 'video-gen')")
    print("4. Set role to 'read'")
    print("5. Click 'Generate token'")
    print("6. Copy the token")
    print("7. Add to .env file: HUGGINGFACE_TOKEN=hf_YourTokenHere")
    print("\n100% FREE - No credit card required!")
    exit(1)

print(f"\nHugging Face Token: Set")

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
print("STEP 2: Generate FREE Videos with Hugging Face")
print("="*70)
print("Using Stable Video Diffusion - completely free!")
print("Each video takes 30s-2min (first time may take longer)")
print("="*70)

# Initialize service
service = HuggingFaceVideoService()

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
print(f"Cost: $0.00 (FREE!)")

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
    print(f"\nSuccess! Check outputs/videos/ for your FREE generated videos!")
else:
    print(f"\nNo videos generated. Check errors above.")
    print("Note: First-time model loading can take a few minutes. Try again!")
