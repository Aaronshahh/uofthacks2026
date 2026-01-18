"""
GPT Image 1 - Ultra-Realistic Crime Documentary Reconstruction
Generates photorealistic 1990s CCTV-style surveillance footage frames
"""
import os
import requests
import base64
from pathlib import Path
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class SurveillanceImageGenerator:
    """
    Generates ultra-realistic reconstructed surveillance footage using GPT Image 1.
    Styled as authentic 1990s CCTV security camera footage.
    """
    
    def __init__(self, output_dir: str = "outputs/images"):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")
        
        self.client = OpenAI(api_key=api_key)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Ultra-realistic 1990s CCTV style system prompt
        self.style_prompt = """PHOTOREALISTIC 1990s CCTV SURVEILLANCE FOOTAGE RECONSTRUCTION.

CAMERA SPECIFICATIONS:
- Authentic 1990s CCD security camera sensor quality
- 480i interlaced video resolution, captured as still frame
- Visible scan lines and interlacing artifacts
- Heavy video noise and analog grain throughout
- Slight motion blur on moving subjects
- Barrel distortion from wide-angle security lens
- Chromatic aberration at frame edges

COLOR GRADING:
- Authentic VHS/CCTV color science: desaturated, slightly green-tinted
- Low dynamic range with crushed shadows
- Blooming highlights around bright light sources
- Color bleeding and smearing typical of 1990s video
- Muddy mid-tones, poor color separation

LIGHTING:
- Harsh overhead fluorescent museum lighting
- Strong shadows from ceiling-mounted fixtures
- Mixed color temperature (warm incandescent + cool fluorescent)
- Low-light amplification artifacts in darker areas

OVERLAY ELEMENTS (MUST APPEAR):
- Red "REC" indicator with pulsing dot in upper right
- Camera designation "CAM XX" in upper left in period-accurate font
- Timestamp "MAR 18 1990 XX:XX:XX AM" in bottom right
- All text in authentic 1990s security system typography (blocky, pixelated)

COMPOSITION:
- High ceiling corner mount perspective (bird's eye angle)
- Ultra-wide angle lens with fisheye distortion
- Typical security camera field of view covering entire room

SUBJECTS:
- Two adult males in authentic 1990 Boston Police uniforms
- Navy blue uniforms with peaked caps and silver badges
- Faces naturally obscured by: cap brims casting shadows, low resolution, motion blur, or turned away
- Period-accurate clothing, equipment, and posture

SETTING:
- Isabella Stewart Gardner Museum interior
- Venetian Gothic palace architecture
- Ornate gilded frames, tapestries, period furniture
- Authentic museum gallery environment

CRITICAL: This must look like an ACTUAL frame of recovered security footage from 1990, not an artistic interpretation. Maximum photorealism with all period-accurate video artifacts."""

    def generate_frames(self, report_text: str) -> Dict[str, Any]:
        """
        Generate 5 sequential ultra-realistic surveillance frames based on the police report.
        """
        # First, use GPT to create 5 detailed scene descriptions
        scene_prompt = f"""Based on this police report about the 1990 Isabella Stewart Gardner Museum heist, 
create 5 sequential scene descriptions for ultra-realistic reconstructed surveillance footage frames.

Report:
{report_text}

Create exactly 5 scenes showing the documented progression of events:
1. ENTRY - The two men posing as police officers arrive at the side entrance
2. DUTCH ROOM - Activity in the Dutch Room where Vermeer and Rembrandt works were taken
3. ART REMOVAL - The actual removal of artwork from frames/walls
4. SHORT GALLERY - Movement through the Short Gallery where Degas works were taken
5. EXIT - The departure from the museum with stolen items

For each scene provide:
- Camera designation (CAM 01 through CAM 05)
- Exact timestamp (between 1:24 AM and 2:45 AM, accurate to seconds)
- Detailed scene description including:
  - Exact museum location/gallery name
  - What the two men in police uniforms are specifically doing
  - Specific artworks visible if relevant (The Concert, Storm on the Sea of Galilee, etc.)
  - Body positions, movements, actions
  - Environmental details (empty frames, displaced furniture, etc.)

IMPORTANT DETAILS:
- Two men in authentic 1990 Boston Police uniforms with peaked caps
- Their faces should be naturally obscured (shadows from caps, turned away, motion blur)
- Focus on the documented theft actions, NOT violence
- Include specific artwork names from the actual heist when relevant
- Authentic museum architecture and furnishings

Output as JSON:
{{"scenes": [
  {{"camera": "CAM 01", "time": "01:24:17 AM", "scene": "detailed description..."}},
  ...
]}}
"""

        print("Generating scene descriptions...")
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a forensic video analyst creating precise scene descriptions for reconstructing authentic surveillance footage from the 1990 Gardner Museum heist. Your descriptions must be historically accurate and cinematically detailed. Output valid JSON only."},
                    {"role": "user", "content": scene_prompt}
                ],
                temperature=0.4,
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
            # Fallback scenes with high detail
            scenes = [
                {"camera": "CAM 01", "time": "01:24:17 AM", "scene": "Museum side entrance on Palace Road. Two figures in Boston Police uniforms approach the security door. One speaks into the intercom while the other stands slightly behind. The peaked caps cast shadows over their faces. A security guard can be seen through the glass door responding to the intercom."},
                {"camera": "CAM 02", "time": "01:47:33 AM", "scene": "Dutch Room gallery interior. Both men in police uniforms stand before the east wall where Vermeer's 'The Concert' hangs in its ornate gilded frame. One man examines the frame edges while the other surveys the room. The Rembrandt self-portrait is visible on the adjacent wall."},
                {"camera": "CAM 03", "time": "02:08:45 AM", "scene": "Dutch Room - art removal in progress. One uniformed figure carefully lifts Rembrandt's 'Storm on the Sea of Galilee' away from the wall, the ornate frame catching the overhead fluorescent light. The other man holds a utility knife, canvas material visible on the floor. Empty frame where The Concert hung now visible."},
                {"camera": "CAM 04", "time": "02:28:12 AM", "scene": "Short Gallery corridor. Both uniformed figures move through the narrow gallery, one carrying rolled canvas under his arm. On the walls, empty frames mark where Degas sketches hung. The bronze Chinese beaker (Ku) is missing from its display pedestal in the foreground."},
                {"camera": "CAM 05", "time": "02:41:56 AM", "scene": "Service corridor near the Palace Road exit. The two men in police uniforms walk toward the exit door, carrying several items. One has rolled canvases, the other carries the Napoleonic eagle finial. Their caps still obscure their faces as they approach the door."}
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
            timestamp = scene.get("time", f"0{i+1}:{30+i*15}:00 AM")
            description = scene.get("scene", scene.get("description", "Museum interior"))
            
            print(f"\n{'─' * 60}")
            print(f"Generating Frame {i+1}/5: {camera} @ {timestamp}")
            print(f"Scene: {description[:80]}...")
            
            # Build the ultra-realistic image prompt
            image_prompt = f"""{self.style_prompt}

SPECIFIC SCENE TO GENERATE:
{description}

MANDATORY OVERLAY TEXT:
- "{camera}" - upper left corner, white blocky security font
- "REC ●" - upper right corner, red text with recording indicator
- "MAR 18 1990 {timestamp}" - lower right corner, white security timestamp font

Generate this as an authentic frame of 1990s CCTV security footage. Maximum photorealism. 
This should be indistinguishable from actual recovered surveillance video from 1990."""

            try:
                # Try gpt-image-1 first (latest model), fall back to dall-e-3
                try:
                    response = self.client.images.generate(
                        model="gpt-image-1",
                        prompt=image_prompt,
                        size="1536x1024",  # Wide surveillance aspect ratio
                        quality="high",
                        n=1
                    )
                except Exception as model_error:
                    if "model" in str(model_error).lower():
                        print(f"  Falling back to dall-e-3...")
                        response = self.client.images.generate(
                            model="dall-e-3",
                            prompt=image_prompt,
                            size="1792x1024",
                            quality="hd",
                            n=1
                        )
                    else:
                        raise model_error
                
                # Handle response - could be URL or base64
                image_data = response.data[0]
                output_path = self.output_dir / f"frame_{i+1}_{camera.replace(' ', '_')}.png"
                
                if hasattr(image_data, 'b64_json') and image_data.b64_json:
                    # Base64 encoded image
                    img_bytes = base64.b64decode(image_data.b64_json)
                    with open(output_path, "wb") as f:
                        f.write(img_bytes)
                elif hasattr(image_data, 'url') and image_data.url:
                    # URL to download
                    img_response = requests.get(image_data.url, timeout=60)
                    img_response.raise_for_status()
                    with open(output_path, "wb") as f:
                        f.write(img_response.content)
                else:
                    raise ValueError("No image data in response")
                
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
    
    print("=" * 60)
    print("GPT IMAGE 1 - ULTRA-REALISTIC SURVEILLANCE RECONSTRUCTION")
    print("=" * 60)
    
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
