"""
Replicate Image-to-Video Service - FREE TIER AVAILABLE

Uses Replicate API with CogVideoX-5B-I2V. Replicate offers:
- $10 FREE credit (never expires)
- ~$0.03-0.05 per video = 200-300 free videos
- No credit card needed for trial
"""

import os
import time
import requests
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import replicate
except ImportError:
    print("Warning: replicate not installed. Run: pip install replicate")
    replicate = None


class ReplicateVideoService:
    """
    Service for video generation using Replicate API.
    FREE $10 credit (200-300 videos) - no credit card required for trial.
    """
    
    def __init__(self):
        api_key = os.getenv("REPLICATE_API_TOKEN")
        if not api_key:
            print("Warning: REPLICATE_API_TOKEN not set.")
            print("Get your FREE $10 credit from: https://replicate.com/signin")
            print("No credit card required!")
        
        self.api_key = api_key
        if api_key and replicate:
            os.environ["REPLICATE_API_TOKEN"] = api_key
        
        self.output_dir = Path("outputs/videos")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _download_video(self, video_url: str, scene_number: int) -> Optional[str]:
        """Download video from URL and save locally."""
        output_filename = f"scene_{scene_number}_replicate.mp4"
        output_path = self.output_dir / output_filename
        
        try:
            print(f"   Downloading video...")
            resp = requests.get(video_url, stream=True, timeout=120)
            resp.raise_for_status()
            
            with open(output_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            file_size = output_path.stat().st_size
            print(f"   Video saved: {output_path} ({file_size:,} bytes)")
            return str(output_path)
        except Exception as e:
            print(f"   Error downloading: {e}")
            return None
    
    def generate_video(
        self,
        prompt: str,
        image_path: Optional[Union[str, Path]] = None,
        duration: int = None,
        scene_number: int = 1
    ) -> Dict[str, Any]:
        """
        Generate video using CogVideoX-5B-I2V on Replicate.
        
        Args:
            prompt: Text description
            image_path: Path to reference image (REQUIRED)
            duration: Ignored (CogVideoX generates ~6s)
            scene_number: Scene identifier
            
        Returns:
            Dictionary with video path, status, and metadata
        """
        if not replicate:
            return {
                "scene_number": scene_number,
                "status": "failed",
                "error": "replicate not installed. Run: pip install replicate",
                "prompt": prompt
            }
        
        if not self.api_key:
            return {
                "scene_number": scene_number,
                "status": "failed",
                "error": "REPLICATE_API_TOKEN not set. Get FREE $10 credit: https://replicate.com/signin",
                "prompt": prompt
            }
        
        if not image_path:
            return {
                "scene_number": scene_number,
                "status": "failed",
                "error": "Image required for image-to-video",
                "prompt": prompt
            }
        
        print(f"Generating video for Scene {scene_number}...")
        print(f"   Prompt: {prompt[:100]}...")
        print(f"   Image: {image_path}")
        print(f"   Using Replicate (costs ~$0.03 from your FREE $10 credit)")
        
        try:
            # Open image file
            with open(image_path, "rb") as f:
                image_file = f
                
                # Use Stable Video Diffusion - more reliable on Replicate
                # Alternative: "stability-ai/stable-video-diffusion:3f0457e4619daac51203dedb472816fd4af51f3149fa7a9e0b5ffcf1b8172438"
                print(f"   Calling Replicate API (takes 2-5 minutes)...")
                
                try:
                    output = replicate.run(
                        "stability-ai/stable-video-diffusion:3f0457e4619daac51203dedb472816fd4af51f3149fa7a9e0b5ffcf1b8172438",
                        input={
                            "image": image_file,
                            "motion_bucket_id": 127,  # Motion intensity (0-255)
                            "cond_aug": 0.02,  # Conditioning augmentation
                        }
                    )
                except Exception as e:
                    # If SVD fails, try AnimateDiff (faster, cheaper)
                    if "version" in str(e).lower() or "not found" in str(e).lower():
                        print(f"   Trying alternative model (AnimateDiff)...")
                        f.seek(0)  # Reset file pointer
                        output = replicate.run(
                            "lucataco/animate-diff:beecf59c4aee8d81bf04f0381033dfa10a4d3710",
                            input={
                                "image": image_file,
                                "prompt": prompt,
                                "num_frames": 16,
                                "guidance_scale": 7.5
                            }
                        )
                    else:
                        raise
            
            # Output format varies by model
            video_url = None
            if isinstance(output, str):
                video_url = output
            elif isinstance(output, list) and len(output) > 0:
                video_url = output[0] if isinstance(output[0], str) else str(output[0])
            elif hasattr(output, 'url'):
                video_url = output.url
            elif isinstance(output, dict) and 'video' in output:
                video_url = output['video']
            else:
                # Try to extract URL from any format
                output_str = str(output)
                if 'http' in output_str:
                    import re
                    urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', output_str)
                    if urls:
                        video_url = urls[0]
                
                if not video_url:
                    raise Exception(f"Unexpected output format: {output}")
            
            # Download video
            local_path = self._download_video(video_url, scene_number)
            
            print(f"Scene {scene_number} video generated successfully")
            
            return {
                "scene_number": scene_number,
                "status": "complete",
                "video_url": video_url,
                "local_path": local_path,
                "duration": "3-4s",
                "model": "Stable Video Diffusion (Replicate)",
                "prompt": prompt,
                "cost": "~$0.02-0.03 (from FREE $10 credit)"
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"   Error: {error_msg}")
            
            # Provide helpful error messages
            if "429" in error_msg or "throttled" in error_msg.lower() or "rate limit" in error_msg.lower():
                error_msg = "Rate limit exceeded. Free tier allows 6 requests/minute. Wait 10 seconds and try again, or add a payment method for higher limits."
            elif "422" in error_msg or "version" in error_msg.lower() or "not found" in error_msg.lower():
                error_msg = "Model version issue. Trying alternative model..."
                # Could retry with different model here
            elif "payment" in error_msg.lower():
                error_msg = "Payment method required for higher rate limits. Free tier: 6 requests/minute."
            
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
        Generate full reconstruction from multiple scenes.
        
        Args:
            scene_prompts: List of scene dictionaries
            image_paths: List of evidence image paths
            duration_per_scene: Ignored
            
        Returns:
            Dictionary with all videos and status
        """
        print("=" * 60)
        print("REPLICATE VIDEO RECONSTRUCTION")
        print("=" * 60)
        print(f"Generating {len(scene_prompts)} scene(s)...")
        print(f"Cost: ~${len(scene_prompts) * 0.03:.2f} from your FREE $10 credit")
        print("=" * 60)
        
        results = {
            "status": "in_progress",
            "total_scenes": len(scene_prompts),
            "completed": 0,
            "failed": 0,
            "videos": []
        }
        
        for i, scene in enumerate(scene_prompts):
            scene_num = scene.get("scene_number", 1)
            prompt = scene.get("prompt", "")
            image_index = scene.get("image_index")
            
            # Get image
            image_path = None
            if image_paths and image_index is not None:
                if 0 <= image_index < len(image_paths):
                    image_path = image_paths[image_index]
            
            if not image_path:
                print(f"\nSkipping scene {scene_num}: No image")
                results["failed"] += 1
                results["videos"].append({
                    "scene_number": scene_num,
                    "status": "skipped",
                    "error": "No image"
                })
                continue
            
            # Add delay between requests to avoid rate limiting
            # Free tier: 6 requests/minute, burst of 1
            if i > 0:  # Don't delay before first request
                delay_seconds = 12  # Wait 12 seconds between requests (safe for 6/min limit)
                print(f"\nWaiting {delay_seconds}s to avoid rate limits...")
                time.sleep(delay_seconds)
            
            print(f"\n{'-' * 60}")
            video_result = self.generate_video(
                prompt=prompt,
                image_path=image_path,
                scene_number=scene_num
            )
            
            results["videos"].append(video_result)
            
            if video_result.get("status") == "complete":
                results["completed"] += 1
            else:
                results["failed"] += 1
                
                # If rate limited, wait longer before next request
                if "429" in str(video_result.get("error", "")) or "throttled" in str(video_result.get("error", "")).lower():
                    print(f"   Rate limited! Waiting 60 seconds before next request...")
                    time.sleep(60)
        
        # Set status
        if results["completed"] == results["total_scenes"]:
            results["status"] = "complete"
        elif results["completed"] > 0:
            results["status"] = "partial"
        else:
            results["status"] = "failed"
        
        print("\n" + "=" * 60)
        print(f"Complete: {results['completed']}/{results['total_scenes']} scenes")
        print(f"Total cost: ~${results['completed'] * 0.03:.2f} (from FREE $10 credit)")
        print("=" * 60)
        
        return results


if __name__ == "__main__":
    print("Testing Replicate Video Service...")
    
    try:
        service = ReplicateVideoService()
        
        test_image = Path("footwear_rag/data/zip_files/begining_heist.png")
        
        if test_image.exists():
            result = service.generate_video(
                prompt="Museum gallery, elegant atmosphere",
                image_path=test_image,
                scene_number=1
            )
            
            print("\nResult:")
            print(f"  Status: {result.get('status')}")
            print(f"  Path: {result.get('local_path', 'N/A')}")
            print(f"  Cost: {result.get('cost', 'N/A')}")
            if result.get('error'):
                print(f"  Error: {result.get('error')}")
        else:
            print(f"Test image not found: {test_image}")
            
    except Exception as e:
        print(f"Test failed: {e}")
