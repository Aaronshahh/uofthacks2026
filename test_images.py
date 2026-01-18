"""
Generate 5 reconstructed surveillance footage frames
1990s CCTV style - Isabella Stewart Gardner Museum Heist
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from image_generator import SurveillanceImageGenerator

load_dotenv()

print("=" * 70)
print("SURVEILLANCE FOOTAGE RECONSTRUCTION")
print("Isabella Stewart Gardner Museum - March 18, 1990")
print("=" * 70)

if not os.getenv("OPENAI_API_KEY"):
    print("ERROR: OPENAI_API_KEY not set")
    exit(1)

report_path = Path("footwear_rag/data/zip_files/message.txt")

if not report_path.exists():
    print(f"ERROR: Report not found: {report_path}")
    exit(1)

print(f"\nReport: {report_path}")
print("Style: 1990s CCTV security camera footage")
print("Output: 5 sequential frames")
print("=" * 70)

# Load report
with open(report_path, 'r', encoding='utf-8') as f:
    report_text = f.read()

# Generate frames
generator = SurveillanceImageGenerator()
results = generator.generate_frames(report_text)

# Results
print("\n" + "=" * 70)
print("GENERATION COMPLETE")
print("=" * 70)
print(f"Status: {results['status']}")
print(f"Frames: {results['completed']}/{results['total']}")

if results['completed'] > 0:
    print(f"\nImages saved to: outputs/images/")
    print("\nGenerated Frames:")
    for img in results['images']:
        if img['status'] == 'complete':
            print(f"\n  {img['camera']} - {img['timestamp']}")
            print(f"  {img['description'][:60]}...")
            print(f"  File: {img['path']}")

print("=" * 70)
