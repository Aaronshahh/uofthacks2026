"""
Hugging Face Spaces Video Service - 100% FREE

Uses Gradio Client to access FREE public Hugging Face Spaces.
NO API key, NO signup, NO costs - completely free!
"""

import os
import time
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

try:
    from gradio_client import Client, handle_file
except ImportError:
    print("ERROR: gradio_client not installed")
    print("Run: pip install gradio_client")
    Client = None


class SpaceVideoService:
    """
    100% FREE video generation using public Hugging Face Spaces.
    No API key needed. No signup. No costs.
    """
    
    def __init__(self):
        # Available FREE Hugging Face Spaces for image-to-video
        self.spaces = {
            "cogvideox": "THUDM/CogVideoX-5B-Space",  # Official CogVideoX demo
            "animatediff": "guoyww/AnimateDiff",  # Fast animation
        }
        
        self.default_space = "cogvideox"
        self.output_dir = Path("outputs/videos")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_video(
        self,
        prompt: str,
        image_path: Optional[Union[str, Path]] = None,
        duration: int = None,
        scene_number: int = 1
    ) -> Dict[str, Any]:
        """
        Generate video using FREE Hugging Face Space.
        
        Args:
            prompt: Text description
            image_path: Path to reference image (REQUIRED)
            duration: Ignored (model determines)
            scene_number: Scene identifier
            
        Returns:
            Dictionary with video path, status, and metadata
        """
        if not Client:
            return {
                "scene_number": scene_number,
                "status": "failed",
                "error": "gradio_client not installed. Run: pip install gradio_client",
                "prompt": prompt
            }
        
        if not image_path:
            return {
                "scene_number": scene_number,
                "status": "failed",
                "error": "Image required",
                "prompt": prompt
            }
        
        print(f"Generating video for Scene {scene_number}...")
        print(f"   Prompt: {prompt[:100]}...")
        print(f"   Image: {image_path}")
        print(f"   Using FREE Hugging Face Space (no API key needed!)")
        
        try:
            # Connect to CogVideoX Space
            space_id = self.spaces[self.default_space]
            print(f"   Connecting to Space: {space_id}")
            client = Client(space_id)
            
            # Call the Space (this is FREE!)
            print(f"   Generating video (takes 2-5 minutes, be patient)...")
            print(f"   Queue position: waiting...")
            
            # Try to call without specifying api_name (use default endpoint)
            try:
                result = client.predict(
                    prompt,
                    handle_file(str(image_path))
                )
            except Exception as e1:
                # Try with common API names
                try:
                    result = client.predict(
                        prompt,
                        handle_file(str(image_path)),
                        api_name="/generate"
                    )
                except Exception as e2:
                    # If both fail, raise the original error with more info
                    raise Exception(f"Could not call Space API. Try 1: {str(e1)[:100]}, Try 2: {str(e2)[:100]}")
            
            # Result is path to generated video
            if isinstance(result, str):
                video_path = result
            elif isinstance(result, dict) and 'video' in result:
                video_path = result['video']
            elif isinstance(result, list) and len(result) > 0:
                video_path = result[0]
            else:
                raise Exception(f"Unexpected result format: {result}")
            
            # Copy video to our output folder
            output_filename = f"scene_{scene_number}_space.mp4"
            output_path = self.output_dir / output_filename
            
            import shutil
            shutil.copy(video_path, output_path)
            
            file_size = output_path.stat().st_size
            print(f"   Video saved: {output_path} ({file_size:,} bytes)")
            
            return {
                "scene_number": scene_number,
                "status": "complete",
                "local_path": str(output_path),
                "duration": "~6s",
                "model": "CogVideoX-5B (via Space)",
                "prompt": prompt,
                "cost": "FREE (100%)"
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"   Error: {error_msg}")
            
            # Provide helpful error messages
            if "queue" in error_msg.lower():
                error_msg = "Space is busy. Try again in a few minutes."
            elif "timeout" in error_msg.lower():
                error_msg = "Request timed out. Space might be overloaded."
            
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
        Generate full reconstruction using FREE Spaces.
        
        Args:
            scene_prompts: List of scene dictionaries
            image_paths: List of image paths
            duration_per_scene: Ignored
            
        Returns:
            Dictionary with all videos and status
        """
        print("=" * 60)
        print("HUGGING FACE SPACE VIDEO RECONSTRUCTION")
        print("100% FREE - No API key, no signup, no costs!")
        print("=" * 60)
        print(f"Generating {len(scene_prompts)} scene(s)...")
        print("Note: Each video takes 2-5 minutes")
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
        
        # Set status
        if results["completed"] == results["total_scenes"]:
            results["status"] = "complete"
        elif results["completed"] > 0:
            results["status"] = "partial"
        else:
            results["status"] = "failed"
        
        print("\n" + "=" * 60)
        print(f"Complete: {results['completed']}/{results['total_scenes']} scenes")
        print(f"Total cost: $0.00 (100% FREE!)")
        print("=" * 60)
        
        return results


if __name__ == "__main__":
    print("Testing FREE Hugging Face Space...")
    
    try:
        service = SpaceVideoService()
        
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
