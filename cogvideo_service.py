"""
CogVideoX Image-to-Video Service

Uses fal.ai API to run CogVideoX-5B-I2V model for video generation.
Open-source alternative to Sora with no content moderation.
"""

import os
import base64
import time
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from PIL import Image
import io

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import fal_client
except ImportError:
    print("Warning: fal_client not installed. Run: pip install fal-client")
    fal_client = None


class CogVideoService:
    """
    Service for generating crime scene reconstruction videos using CogVideoX-5B-I2V.
    Uses fal.ai API for hosted inference.
    """
    
    def __init__(self):
        api_key = os.getenv("FAL_KEY")
        if not api_key:
            print("Warning: FAL_KEY environment variable not set.")
            print("Get your API key from: https://fal.ai/dashboard/keys")
        
        self.api_key = api_key
        self.model = "fal-ai/cogvideox-5b/image-to-video"
        self.default_duration = 6  # seconds (CogVideoX generates ~6s videos)
        self.default_size = (1280, 720)  # CogVideoX supports flexible sizes
        self.output_dir = Path("outputs/videos")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _upload_image_to_fal(self, image_path: Union[str, Path]) -> str:
        """
        Upload image to fal.ai storage and return URL.
        """
        if not fal_client:
            raise ImportError("fal_client not installed")
        
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        print(f"   Uploading image to fal.ai...")
        
        # Read image bytes
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        
        # Upload to fal storage
        url = fal_client.upload(image_bytes, "image/png")
        print(f"   Image uploaded: {url[:60]}...")
        
        return url
    
    def _download_video(self, video_url: str, scene_number: int) -> Optional[str]:
        """Download video from URL and save locally."""
        import requests
        
        output_filename = f"scene_{scene_number}_cogvideo.mp4"
        output_path = self.output_dir / output_filename
        
        try:
            print(f"   Downloading video...")
            resp = requests.get(video_url, stream=True, timeout=120)
            resp.raise_for_status()
            
            with open(output_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            file_size = output_path.stat().st_size
            print(f"   Video saved to {output_path} ({file_size:,} bytes)")
            return str(output_path)
        except Exception as e:
            print(f"   Error downloading video: {e}")
            return None
    
    def generate_video(
        self,
        prompt: str,
        image_path: Optional[Union[str, Path]] = None,
        duration: int = None,
        scene_number: int = 1,
        num_inference_steps: int = 50,
        guidance_scale: float = 6.0
    ) -> Dict[str, Any]:
        """
        Generate a video for a single scene using CogVideoX via fal.ai.
        
        Args:
            prompt: Text description of the desired animation
            image_path: Path to reference image (REQUIRED for image-to-video)
            duration: Video duration (CogVideoX generates ~6s videos)
            scene_number: Scene identifier for output naming
            num_inference_steps: Quality vs speed tradeoff (default 50)
            guidance_scale: How closely to follow the prompt (default 6.0)
            
        Returns:
            Dictionary with video path, status, and metadata
        """
        if not fal_client:
            return {
                "scene_number": scene_number,
                "status": "failed",
                "error": "fal_client not installed. Run: pip install fal-client",
                "prompt": prompt
            }
        
        if not self.api_key:
            return {
                "scene_number": scene_number,
                "status": "failed",
                "error": "FAL_KEY not set. Get key from https://fal.ai/dashboard/keys",
                "prompt": prompt
            }
        
        if not image_path:
            return {
                "scene_number": scene_number,
                "status": "failed",
                "error": "Image required for CogVideoX image-to-video model",
                "prompt": prompt
            }
        
        print(f"Generating video for Scene {scene_number}...")
        print(f"   Prompt: {prompt[:100]}...")
        print(f"   Reference image: {image_path}")
        
        try:
            # Upload image to fal.ai
            image_url = self._upload_image_to_fal(image_path)
            
            # Call CogVideoX model via fal.ai
            print(f"   Calling CogVideoX-5B-I2V API (this takes 2-5 minutes)...")
            
            # Set FAL_KEY env var for fal_client
            os.environ["FAL_KEY"] = self.api_key
            
            result = fal_client.subscribe(
                self.model,
                arguments={
                    "prompt": prompt,
                    "image_url": image_url,
                    "num_inference_steps": num_inference_steps,
                    "guidance_scale": guidance_scale,
                    "use_rife": False,  # RIFE frame interpolation (slower but smoother)
                    "export_fps": 8  # 8 fps for 6 second videos
                },
                with_logs=True,
                on_queue_update=lambda update: print(f"   Queue position: {update.get('position', '?')}")
            )
            
            # Extract video URL from result
            video_url = result.get("video", {}).get("url")
            
            if not video_url:
                raise Exception(f"No video URL in response: {result}")
            
            # Download video
            local_path = self._download_video(video_url, scene_number)
            
            print(f"Scene {scene_number} video generated successfully")
            
            return {
                "scene_number": scene_number,
                "status": "complete",
                "video_url": video_url,
                "local_path": local_path,
                "duration": 6,  # CogVideoX generates ~6s videos
                "size": "variable",
                "prompt": prompt,
                "model": "CogVideoX-5B-I2V"
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"Error generating video for Scene {scene_number}: {error_msg}")
            
            return {
                "scene_number": scene_number,
                "status": "failed",
                "error": error_msg,
                "prompt": prompt
            }
    
    def generate_reconstruction(
        self,
        scene_prompts: List[Dict[str, Any]],
        image_paths: Optional[List[Union[str, Path]]] = None,
        duration_per_scene: int = None
    ) -> Dict[str, Any]:
        """
        Generate a full crime scene reconstruction from multiple scenes.
        
        Args:
            scene_prompts: List of scene prompt dictionaries from SceneParser
            image_paths: Optional list of evidence image paths
            duration_per_scene: Duration for each scene video (ignored, CogVideoX is ~6s)
            
        Returns:
            Dictionary with all videos and overall status
        """
        print("=" * 60)
        print("COGVIDEOX VIDEO RECONSTRUCTION")
        print("=" * 60)
        print(f"Generating {len(scene_prompts)} scene(s)...")
        
        results = {
            "status": "in_progress",
            "total_scenes": len(scene_prompts),
            "completed": 0,
            "failed": 0,
            "videos": []
        }
        
        for scene in scene_prompts:
            scene_num = scene.get("scene_number", 1)
            prompt = scene.get("prompt", "")
            image_index = scene.get("image_index")
            
            # Get corresponding image if available
            image_path = None
            if image_paths and image_index is not None:
                if 0 <= image_index < len(image_paths):
                    image_path = image_paths[image_index]
            
            if not image_path:
                print(f"Skipping scene {scene_num}: No image provided")
                results["failed"] += 1
                results["videos"].append({
                    "scene_number": scene_num,
                    "status": "skipped",
                    "error": "No reference image available"
                })
                continue
            
            # Generate video for this scene
            video_result = self.generate_video(
                prompt=prompt,
                image_path=image_path,
                scene_number=scene_num
            )
            
            # Track results
            results["videos"].append(video_result)
            
            if video_result.get("status") == "complete":
                results["completed"] += 1
            else:
                results["failed"] += 1
        
        # Set overall status
        if results["completed"] == results["total_scenes"]:
            results["status"] = "complete"
        elif results["completed"] > 0:
            results["status"] = "partial"
        else:
            results["status"] = "failed"
        
        print("=" * 60)
        print(f"Reconstruction Complete: {results['completed']}/{results['total_scenes']} scenes")
        print("=" * 60)
        
        return results


if __name__ == "__main__":
    # Test the CogVideo service
    print("Testing CogVideoX Service...")
    
    try:
        service = CogVideoService()
        
        # Test with a sample image if available
        test_image = Path("footwear_rag/data/zip_files/begining_heist.png")
        
        if test_image.exists():
            result = service.generate_video(
                prompt="Art museum investigation documentary. Elegant museum gallery. Professional mysterious cinematography.",
                image_path=test_image,
                scene_number=1
            )
            
            print("\nResult:")
            print(f"  Status: {result.get('status')}")
            print(f"  Local path: {result.get('local_path', 'N/A')}")
            if result.get('error'):
                print(f"  Error: {result.get('error')}")
        else:
            print(f"Test image not found at {test_image}")
            
    except Exception as e:
        print(f"Test failed: {e}")
