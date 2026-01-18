"""
Simple Replicate test - one image at a time with rate limit handling
"""
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from replicate_video_service import ReplicateVideoService

load_dotenv()

if not os.getenv("REPLICATE_API_TOKEN"):
    print("ERROR: REPLICATE_API_TOKEN not set in .env")
    exit(1)

service = ReplicateVideoService()

# Test with one image first
test_image = Path("footwear_rag/data/zip_files/begining_heist.png")

if not test_image.exists():
    print(f"ERROR: Image not found: {test_image}")
    exit(1)

print("="*70)
print("Testing Replicate with ONE image first")
print("="*70)
print(f"Image: {test_image.name}")
print(f"\nNote: Free tier allows 6 requests/minute")
print("Waiting 12 seconds between requests to stay under limit")
print("="*70)

result = service.generate_video(
    prompt="Art museum investigation documentary. Elegant museum gallery entrance. Professional mysterious cinematography.",
    image_path=test_image,
    scene_number=1
)

print("\n" + "="*70)
print("RESULT")
print("="*70)
print(f"Status: {result['status']}")

if result['status'] == 'complete':
    print(f"Video saved: {result['local_path']}")
    print(f"Model: {result['model']}")
    print(f"Cost: {result['cost']}")
    print("\nSuccess! You can now run the full test with all images.")
    print("Run: python test_replicate.py")
else:
    error = result.get('error', 'Unknown error')
    print(f"Error: {error}")
    
    if "rate limit" in error.lower() or "429" in error:
        print("\nRate limit hit! Options:")
        print("1. Wait 60 seconds and try again")
        print("2. Add a payment method to Replicate for higher limits")
        print("3. Run images one at a time with 12s delays")
    elif "payment" in error.lower():
        print("\nTo get higher rate limits:")
        print("1. Go to: https://replicate.com/account/billing")
        print("2. Add a payment method (you still get $10 free credit)")
        print("3. Rate limit increases to 60 requests/minute")
