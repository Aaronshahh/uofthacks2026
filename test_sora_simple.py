"""
Simple Sora test - NO images, just text prompts
Tests if Sora works at all before adding images
"""
import os
from dotenv import load_dotenv
from sora_service import SoraVideoService

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    print("ERROR: OPENAI_API_KEY not set")
    exit(1)

print("="*70)
print("SORA SIMPLE TEST - Text Only (No Images)")
print("="*70)

# Completely neutral, art-only prompt
test_prompt = """
A beautiful Renaissance art gallery in a historic museum. 
Ornate golden frames display classical oil paintings on burgundy walls.
Soft natural light streams through tall windows.
Marble floors reflect the elegant architecture.
Peaceful, serene atmosphere. 4K documentary footage.
"""

print(f"Prompt: {test_prompt.strip()}")
print("="*70)

try:
    service = SoraVideoService()
    
    # Generate WITHOUT any image reference
    result = service.generate_video(
        prompt=test_prompt,
        image_path=None,  # NO IMAGE
        scene_number=1,
        duration=5
    )
    
    print(f"\nStatus: {result['status']}")
    
    if result['status'] == 'complete':
        print(f"Video saved: {result.get('local_path')}")
        print("\nSUCCESS! Text-to-video works.")
        print("The IMAGES are causing the moderation block, not the prompts.")
    elif result['status'] == 'blocked':
        print(f"Error: {result.get('error')}")
        print("\nEven text-only is blocked. Sora moderation is very strict.")
        print("Consider using Replicate instead (has $10 free credit).")
    else:
        print(f"Error: {result.get('error')}")
        
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*70)
