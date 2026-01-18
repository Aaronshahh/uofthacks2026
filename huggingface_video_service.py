"""
Hugging Face Image-to-Video Service - COMPLETELY FREE

Uses Hugging Face Inference API for free image-to-video generation.
No costs, no credits needed, just requires a free Hugging Face account.
"""

import os
import base64
import time
import requests
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from PIL import Image
import io

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class HuggingFaceVideoService:
    """
    Service for generating videos using FREE Hugging Face Inference API.
    Supports multiple image-to-video models with zero cost.
    """
    
    def __init__(self):
        api_key = os.getenv("HUGGINGFACE_TOKEN")
        if not api_key:
            print("Warning: HUGGINGFACE_TOKEN not set.")
            print("Get your FREE token from: https://huggingface.co/settings/tokens")
        
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        
        # Available FREE image-to-video models on Hugging Face
        self.models = {
            "cogvideox": "THUDM/CogVideoX-5b-I2V",  # Best quality
            "animatediff": "guoyww/animatediff-motion-adapter-v1-5-2",  # Fast
            "svd": "stabilityai/stable-video-diffusion-img2vid-xt"  # Good balance
        }
        
        self.default_model = "svd"  # Stable Video Diffusion - good balance
        self.output_dir = Path("outputs/videos")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _image_to_base64(self, image_path: Union[str, Path]) -> str:
        """Convert image to base64 string."""
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        
        return base64.b64encode(image_bytes).decode("utf-8")
    
    def _query_hf_api(self, model_id: str, data: Union[Dict, bytes]) -> bytes:
        """Query Hugging Face Inference API."""
        api_url = f"https://api-inference.huggingface.co/models/{model_id}"
        
        print(f"   Calling Hugging Face API: {model_id}")
        print(f"   This is FREE! May take 30s-2min...")
        
        # HF API might be loading the model for first use
        max_retries = 3
        retry_delay = 20  # seconds
        
        for attempt in range(max_retries):
            # For image-to-video models, send raw bytes as data (not JSON)
            if isinstance(data, bytes):
                response = requests.post(api_url, headers=self.headers, data=data, timeout=180)
            else:
                response = requests.post(api_url, headers=self.headers, json=data, timeout=180)
            
            if response.status_code == 503:
                # Model is loading
                if attempt < max_retries - 1:
                    print(f"   Model loading, retrying in {retry_delay}s... ({attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    continue
                else:
                    raise Exception("Model loading timeout. Try again in a few minutes.")
            
            if response.status_code == 200:
                return response.content
            else:
                try:
                    error_msg = response.json().get("error", response.text)
                except:
                    error_msg = response.text
                raise Exception(f"API error ({response.status_code}): {error_msg}")
        
        raise Exception("Max retries exceeded")
    
    def generate_video_svd(
        self,
        image_path: Union[str, Path],
        prompt: str,
        scene_number: int = 1
    ) -> Dict[str, Any]:
        """
        Generate video using Stable Video Diffusion (FREE).
        Best for general use - good quality, reasonable speed.
        """
        print(f"Generating video for Scene {scene_number} with SVD...")
        print(f"   Prompt: {prompt[:100]}...")
        print(f"   Image: {image_path}")
        
        try:
            # Read image as raw bytes
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            
            # Call Hugging Face Inference API with raw image bytes
            # (SVD expects binary image data, not JSON)
            video_bytes = self._query_hf_api(
                self.models["svd"],
                image_bytes  # Send raw bytes directly
            )
            
            # Save video
            output_filename = f"scene_{scene_number}_hf_svd.mp4"
            output_path = self.output_dir / output_filename
            
            with open(output_path, "wb") as f:
                f.write(video_bytes)
            
            file_size = output_path.stat().st_size
            print(f"   Video saved: {output_path} ({file_size:,} bytes)")
            
            return {
                "scene_number": scene_number,
                "status": "complete",
                "local_path": str(output_path),
                "duration": "3-4s",
                "model": "Stable Video Diffusion",
                "prompt": prompt,
                "cost": "FREE"
            }
            
        except Exception as e:
            print(f"   Error: {e}")
            return {
                "scene_number": scene_number,
                "status": "failed",
                "error": str(e),
                "prompt": prompt
            }
    
    def generate_video(
        self,
        prompt: str,
        image_path: Optional[Union[str, Path]] = None,
        duration: int = None,
        scene_number: int = 1,
        model: str = None
    ) -> Dict[str, Any]:
        """
        Generate a video using FREE Hugging Face models.
        
        Args:
            prompt: Text description (mainly for metadata, some models ignore this)
            image_path: Path to reference image (REQUIRED)
            duration: Ignored (model determines duration)
            scene_number: Scene identifier
            model: Model to use ("svd", "cogvideox", "animatediff")
            
        Returns:
            Dictionary with video path, status, and metadata
        """
        if not self.api_key:
            return {
                "scene_number": scene_number,
                "status": "failed",
                "error": "HUGGINGFACE_TOKEN not set. Get FREE token from https://huggingface.co/settings/tokens",
                "prompt": prompt
            }
        
        if not image_path:
            return {
                "scene_number": scene_number,
                "status": "failed",
                "error": "Image required for image-to-video generation",
                "prompt": prompt
            }
        
        # Use Stable Video Diffusion (best free option)
        return self.generate_video_svd(image_path, prompt, scene_number)
    
    def generate_reconstruction(
        self,
        scene_prompts: List[Dict[str, Any]],
        image_paths: Optional[List[Union[str, Path]]] = None,
        duration_per_scene: int = None
    ) -> Dict[str, Any]:
        """
        Generate a full reconstruction from multiple scenes using FREE HF API.
        
        Args:
            scene_prompts: List of scene prompt dictionaries
            image_paths: List of evidence image paths
            duration_per_scene: Ignored (model determines duration)
            
        Returns:
            Dictionary with all videos and overall status
        """
        print("=" * 60)
        print("HUGGING FACE FREE VIDEO RECONSTRUCTION")
        print("=" * 60)
        print(f"Generating {len(scene_prompts)} scene(s)...")
        print("100% FREE - No costs, no credits needed!")
        print("=" * 60)
        
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
            
            # Get corresponding image
            image_path = None
            if image_paths and image_index is not None:
                if 0 <= image_index < len(image_paths):
                    image_path = image_paths[image_index]
            
            if not image_path:
                print(f"\nSkipping scene {scene_num}: No image provided")
                results["failed"] += 1
                results["videos"].append({
                    "scene_number": scene_num,
                    "status": "skipped",
                    "error": "No reference image"
                })
                continue
            
            print(f"\n{'-' * 60}")
            # Generate video
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
        
        # Set overall status
        if results["completed"] == results["total_scenes"]:
            results["status"] = "complete"
        elif results["completed"] > 0:
            results["status"] = "partial"
        else:
            results["status"] = "failed"
        
        print("\n" + "=" * 60)
        print(f"Reconstruction Complete: {results['completed']}/{results['total_scenes']} scenes")
        print("=" * 60)
        
        return results


if __name__ == "__main__":
    print("Testing Hugging Face FREE Video Service...")
    
    try:
        service = HuggingFaceVideoService()
        
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
            print(f"  Cost: {result.get('cost', 'FREE')}")
            if result.get('error'):
                print(f"  Error: {result.get('error')}")
        else:
            print(f"Test image not found: {test_image}")
            
    except Exception as e:
        print(f"Test failed: {e}")
