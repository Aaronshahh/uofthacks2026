"""
DALL-E Image Generator for Crime Documentary Reconstruction
Generates 1990s CCTV-style surveillance footage frames
"""
import os
import requests
from pathlib import Path
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class SurveillanceImageGenerator:
    """
    Generates reconstructed surveillance footage frames using DALL-E.
    Styled as 1990s CCTV security camera footage.
    """
    
    def __init__(self, output_dir: str = "outputs/images"):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")
        
        self.client = OpenAI(api_key=api_key)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Base style prompt for 1990s CCTV look
        self.style_prompt = """
1990s CCTV security camera footage quality. Low resolution, high grain, video noise, slight motion blur.
Faded desaturated VHS color video style - muddy low-light color palette of early 90s video technology.
Must include digital text overlay in retro font: "CAM [X]", "REC", timestamp "MAR 18 1990".
High-angle wide-angle fisheye lens perspective from ceiling corner.
Dramatic documentary re-enactment. No graphic violence.
"""

    def generate_frames(self, report_text: str) -> Dict[str, Any]:
        """
        Generate 5 sequential surveillance frames based on the police report.
        """
        # First, use GPT to create 5 scene descriptions
        scene_prompt = f"""Based on this police report about the Isabella Stewart Gardner Museum heist, 
create 5 sequential scene descriptions for reconstructed surveillance footage frames.

Report:
{report_text}

Create exactly 5 scenes showing the progression of events:
1. Entry/Arrival scene
2. First gallery scene  
3. Art removal scene
4. Second gallery/movement scene
5. Exit/Departure scene

For each scene, provide:
- Camera number (CAM 01 through CAM 05)
- Timestamp (between 1:24 AM and 2:45 AM on MAR 18 1990)
- Brief description focusing on: location in museum, what the two men in police uniforms are doing, key artwork visible

IMPORTANT: 
- Two men in 1990s police uniforms (peaked caps, badges)
- Faces obscured by shadows/caps/low resolution
- Focus on theft and movement, NOT violence
- Include specific artwork names when relevant (Vermeer, Rembrandt, etc.)

Output as JSON array:
[
  {{"camera": "CAM 01", "time": "01:24 AM", "scene": "description"}},
  ...
]
"""

        print("Generating scene descriptions...")
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a documentary producer creating scene descriptions for reconstructed surveillance footage of the 1990 Gardner Museum heist. Output valid JSON only."},
                    {"role": "user", "content": scene_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            import json
            scenes_data = json.loads(response.choices[0].message.content)
            
            # Handle different JSON structures
            if isinstance(scenes_data, dict):
                scenes = scenes_data.get("scenes", scenes_data.get("frames", list(scenes_data.values())[0] if scenes_data else []))
            else:
                scenes = scenes_data
                
        except Exception as e:
            print(f"Error generating scenes: {e}")
            # Fallback scenes
            scenes = [
                {"camera": "CAM 01", "time": "01:24 AM", "scene": "Museum side entrance. Two figures in police uniforms approach the door."},
                {"camera": "CAM 02", "time": "01:35 AM", "scene": "Dutch Room gallery. Figures examining paintings on the wall."},
                {"camera": "CAM 03", "time": "02:00 AM", "scene": "Gallery interior. Figure carefully removing framed artwork from wall."},
                {"camera": "CAM 04", "time": "02:28 AM", "scene": "Short Gallery. Movement between display cases and walls."},
                {"camera": "CAM 05", "time": "02:41 AM", "scene": "Service corridor. Figures moving toward exit with items."}
            ]
        
        print(f"Generated {len(scenes)} scene descriptions")
        
        # Generate images for each scene
        results = {
            "status": "in_progress",
            "total": len(scenes),
            "completed": 0,
            "failed": 0,
            "images": []
        }
        
        for i, scene in enumerate(scenes[:5]):  # Limit to 5
            camera = scene.get("camera", f"CAM 0{i+1}")
            timestamp = scene.get("time", f"0{i+1}:{30+i*15} AM")
            description = scene.get("scene", scene.get("description", "Museum interior"))
            
            print(f"\n{'─' * 60}")
            print(f"Generating Frame {i+1}/5: {camera} @ {timestamp}")
            print(f"Scene: {description[:80]}...")
            
            # Build the full image prompt
            image_prompt = f"""Reconstructed 1990s CCTV surveillance footage frame.

{self.style_prompt}

SCENE: {description}

OVERLAY TEXT (must appear in image):
- "{camera}" in top left corner
- "REC" with blinking dot indicator
- "MAR 18 1990 {timestamp}" timestamp

Two men in 1990s police uniforms with peaked caps and badges. Faces obscured by shadows, caps, or low resolution grain.
Isabella Stewart Gardner Museum interior - ornate Venetian palace style.
Documentary re-enactment, no violence."""

            try:
                response = self.client.images.generate(
                    model="dall-e-3",
                    prompt=image_prompt,
                    size="1792x1024",  # Wide aspect ratio for surveillance
                    quality="hd",
                    n=1
                )
                
                image_url = response.data[0].url
                
                # Download and save
                output_path = self.output_dir / f"frame_{i+1}_{camera.replace(' ', '_')}.png"
                
                img_response = requests.get(image_url, timeout=60)
                img_response.raise_for_status()
                
                with open(output_path, "wb") as f:
                    f.write(img_response.content)
                
                print(f"  Saved: {output_path}")
                
                results["images"].append({
                    "frame": i + 1,
                    "camera": camera,
                    "timestamp": f"MAR 18 1990 {timestamp}",
                    "description": description,
                    "path": str(output_path),
                    "status": "complete"
                })
                results["completed"] += 1
                
            except Exception as e:
                error_msg = str(e)
                print(f"  ERROR: {error_msg[:100]}")
                
                results["images"].append({
                    "frame": i + 1,
                    "camera": camera,
                    "status": "failed",
                    "error": error_msg
                })
                results["failed"] += 1
        
        # Final status
        if results["completed"] == results["total"]:
            results["status"] = "complete"
        elif results["completed"] > 0:
            results["status"] = "partial"
        else:
            results["status"] = "failed"
        
        return results


if __name__ == "__main__":
    # Test with the report
    report_path = Path("footwear_rag/data/zip_files/message.txt")
    
    if not report_path.exists():
        print(f"Report not found: {report_path}")
        exit(1)
    
    with open(report_path, 'r', encoding='utf-8') as f:
        report_text = f.read()
    
    generator = SurveillanceImageGenerator()
    results = generator.generate_frames(report_text)
    
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Status: {results['status']}")
    print(f"Completed: {results['completed']}/{results['total']} frames")
    
    if results['images']:
        print("\nGenerated Frames:")
        for img in results['images']:
            if img['status'] == 'complete':
                print(f"  Frame {img['frame']}: {img['camera']} @ {img['timestamp']}")
                print(f"    File: {img['path']}")
            else:
                print(f"  Frame {img['frame']}: FAILED - {img.get('error', '')[:50]}")
