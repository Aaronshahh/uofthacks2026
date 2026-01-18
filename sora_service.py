"""
Sora Video Generation Service

Handles video generation using OpenAI's Sora API.
Generates video clips from scene descriptions and evidence images.
"""

import os
import base64
import time
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from openai import OpenAI
from PIL import Image
import io


class SoraVideoService:
    """
    Service for generating crime scene reconstruction videos using OpenAI Sora API.
    """
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is not set. "
                "Please set it to use Sora video generation."
            )
        
        self.client = OpenAI(api_key=api_key)
        self.model = "sora-2"  # Sora model name (use "sora-2-pro" for larger sizes)
        self.default_duration = 5  # seconds per scene
        self.default_size = "1280x720"  # Default Sora video size (landscape HD)
        self.output_dir = Path("outputs/videos")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Valid Sora video sizes (sora-2 only supports 720x1280, 1280x720)
        self.valid_sizes = {
            "sora-2": ["720x1280", "1280x720"],
            "sora-2-pro": ["720x1280", "1280x720", "1024x1792", "1792x1024"]
        }
    
    def _load_image_as_base64(self, image_path: Union[str, Path]) -> str:
        """Load an image file and convert to base64."""
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        
        return base64.standard_b64encode(image_bytes).decode("utf-8")
    
    def _get_image_media_type(self, image_path: Union[str, Path]) -> str:
        """Get the media type based on file extension."""
        ext = Path(image_path).suffix.lower()
        media_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp"
        }
        return media_types.get(ext, "image/png")
    
    def _resize_image_for_sora(self, image_path: Union[str, Path], target_size: str = None) -> Path:
        """
        Resize image to match Sora's required dimensions.
        Returns path to the resized image file.
        """
        if target_size is None:
            target_size = self.default_size
        
        # Parse target dimensions
        width, height = map(int, target_size.split('x'))
        
        # Load and resize image
        img = Image.open(image_path)
        
        # Resize with high-quality resampling
        resized_img = img.resize((width, height), Image.Resampling.LANCZOS)
        
        # Save to temp file
        temp_path = self.output_dir / f"temp_resized_{Path(image_path).name}"
        resized_img.save(temp_path, format='PNG', optimize=True)
        
        print(f"   Resized image from {img.size} to {resized_img.size}")
        return temp_path
    
    def _download_video(self, video_url: str, scene_number: int) -> str:
        """Download video from URL and save locally."""
        import requests
        
        output_filename = f"scene_{scene_number}_reconstruction.mp4"
        output_path = self.output_dir / output_filename
        
        try:
            resp = requests.get(video_url, stream=True, timeout=120)
            resp.raise_for_status()
            
            with open(output_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"   Video saved to {output_path}")
            return str(output_path)
        except Exception as e:
            print(f"   Failed to download video: {e}")
            return None
    
    def generate_video(
        self,
        prompt: str,
        image_path: Optional[Union[str, Path]] = None,
        duration: int = None,
        size: str = None,
        scene_number: int = 1
    ) -> Dict[str, Any]:
        """
        Generate a video for a single scene using Sora API.
        
        Args:
            prompt: Text description of the scene
            image_path: Optional path to reference image
            duration: Video duration in seconds (5-20)
            size: Video size (e.g., "1792x1024", "1280x720")
            scene_number: Scene identifier for output naming
            
        Returns:
            Dictionary with video URL, status, and metadata
        """
        duration = duration or self.default_duration
        size = size or self.default_size
        
        print(f"Generating video for Scene {scene_number}...")
        print(f"   Prompt: {prompt[:100]}...")
        if image_path:
            print(f"   Reference image: {image_path}")
        
        try:
            # Build the request parameters for Sora API
            # Using create_and_poll to wait for completion automatically
            request_params = {
                "model": self.model,
                "prompt": prompt,
                "size": size,  # Specify video dimensions
            }
            
            # If we have a reference image, resize and include it for image-to-video
            resized_image_path = None
            if image_path:
                # Resize image to match Sora's requirements
                resized_image_path = self._resize_image_for_sora(image_path, size)
                
                # Open the resized image file for input_reference parameter
                image_file = open(resized_image_path, "rb")
                request_params["input_reference"] = image_file
            
            # Call Sora API using create_and_poll which waits for completion
            print(f"   Calling Sora API (this may take a few minutes)...")
            response = self.client.videos.create_and_poll(**request_params)
            
            # Close the file and cleanup temp file
            if image_path and 'image_file' in locals():
                image_file.close()
                if resized_image_path and resized_image_path.exists():
                    resized_image_path.unlink()  # Delete temp resized image
            
            # create_and_poll already handles waiting for completion
            # Check if generation succeeded or failed
            if response.error:
                # Moderation or other error
                error_code = response.error.code if hasattr(response.error, 'code') else 'unknown'
                error_msg = response.error.message if hasattr(response.error, 'message') else str(response.error)
                print(f"   Video generation failed: {error_code} - {error_msg}")
                raise Exception(f"{error_code}: {error_msg}")
            
            if response.status != 'completed':
                raise Exception(f"Video generation failed with status: {response.status}")
            
            # Download video content using the video ID
            video_id = response.id
            output_path = None
            
            print(f"   Downloading video content (ID: {video_id})")
            try:
                # Download video content from Sora (returns streaming response)
                video_response = self.client.videos.download_content(video_id)
                
                # Save to file
                output_filename = f"scene_{scene_number}_reconstruction.mp4"
                output_path = self.output_dir / output_filename
                
                # Handle streaming response - read all content
                with open(output_path, "wb") as f:
                    if hasattr(video_response, 'iter_bytes'):
                        # Stream the content
                        for chunk in video_response.iter_bytes(chunk_size=8192):
                            f.write(chunk)
                    elif hasattr(video_response, 'read'):
                        # Read all at once
                        f.write(video_response.read())
                    else:
                        # Try to convert to bytes directly
                        f.write(bytes(video_response))
                
                print(f"   Video saved to {output_path} ({output_path.stat().st_size} bytes)")
            except Exception as download_error:
                print(f"   Error downloading video: {download_error}")
                output_path = None
            
            print(f"Scene {scene_number} video generated successfully")
            
            return {
                "scene_number": scene_number,
                "status": "complete",
                "video_id": response.id if response else None,
                "local_path": str(output_path) if output_path else None,
                "duration": duration,
                "size": size,
                "prompt": prompt
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"Error generating video for Scene {scene_number}: {error_msg}")
            
            # Check for specific error types
            if "content_policy" in error_msg.lower() or "moderation" in error_msg.lower():
                return {
                    "scene_number": scene_number,
                    "status": "blocked",
                    "error": "Content moderation blocked this scene",
                    "prompt": prompt
                }
            elif "rate_limit" in error_msg.lower():
                return {
                    "scene_number": scene_number,
                    "status": "rate_limited",
                    "error": "Rate limit exceeded - try again later",
                    "prompt": prompt
                }
            else:
                return {
                    "scene_number": scene_number,
                    "status": "failed",
                    "error": error_msg,
                    "prompt": prompt
                }
    
    def _poll_for_completion(self, job_id: str, max_wait: int = 300) -> Any:
        """
        Poll for video generation completion.
        
        Args:
            job_id: The generation job ID
            max_wait: Maximum seconds to wait
            
        Returns:
            Completed video result
        """
        print(f"   Waiting for video generation (job: {job_id})...")
        
        start_time = time.time()
        poll_interval = 5  # seconds
        
        while time.time() - start_time < max_wait:
            try:
                result = self.client.videos.retrieve(job_id)
                
                if hasattr(result, 'status'):
                    if result.status == 'completed':
                        return result
                    elif result.status == 'failed':
                        raise Exception(f"Video generation failed: {getattr(result, 'error', 'Unknown error')}")
                    else:
                        print(f"   Status: {result.status}...")
                else:
                    # No status field means it's complete
                    return result
                    
            except Exception as e:
                if "not found" not in str(e).lower():
                    raise
            
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Video generation timed out after {max_wait} seconds")
    
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
            duration_per_scene: Duration for each scene video
            
        Returns:
            Dictionary with all videos and overall status
        """
        print("=" * 60)
        print("SORA VIDEO RECONSTRUCTION")
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
            
            # Generate video for this scene
            video_result = self.generate_video(
                prompt=prompt,
                image_path=image_path,
                duration=duration_per_scene,
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


def generate_from_report(
    report_path: str,
    image_paths: List[str],
    output_dir: str = "outputs/videos"
) -> Dict[str, Any]:
    """
    Convenience function to generate video reconstruction from a report file.
    
    Args:
        report_path: Path to the police report text file
        image_paths: List of evidence image paths in chronological order
        output_dir: Directory to save generated videos
        
    Returns:
        Full reconstruction result dictionary
    """
    from scene_parser import SceneParser
    
    # Parse the report
    print("📄 Parsing police report...")
    with open(report_path, 'r', encoding='utf-8') as f:
        report_text = f.read()
    
    parser = SceneParser()
    parsed = parser.parse_report(report_text, num_images=len(image_paths))
    scene_prompts = parser.generate_video_prompts(parsed)
    
    print(f"   Found {len(scene_prompts)} scenes to reconstruct")
    
    # Generate videos
    service = SoraVideoService()
    service.output_dir = Path(output_dir)
    service.output_dir.mkdir(parents=True, exist_ok=True)
    
    result = service.generate_reconstruction(
        scene_prompts=scene_prompts,
        image_paths=image_paths
    )
    
    # Add parsed scene info to result
    result["parsed_scenes"] = parsed
    result["scene_prompts"] = scene_prompts
    
    return result


if __name__ == "__main__":
    # Test the Sora service with a simple prompt
    print("Testing Sora Video Service...")
    
    try:
        service = SoraVideoService()
        
        test_prompt = (
            "A dimly lit residential kitchen at night. "
            "A chair lies tipped over on the floor near a counter. "
            "The atmosphere is tense and quiet. "
            "Soft shadows from a single overhead light."
        )
        
        result = service.generate_video(
            prompt=test_prompt,
            scene_number=1,
            duration=5
        )
        
        print("\nResult:")
        print(f"  Status: {result.get('status')}")
        print(f"  Video URL: {result.get('video_url', 'N/A')}")
        if result.get('error'):
            print(f"  Error: {result.get('error')}")
            
    except ValueError as e:
        print(f"⚠️ Configuration error: {e}")
    except Exception as e:
        print(f"Test failed: {e}")
