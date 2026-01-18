"""
Scene Parser Module

Parses police reports/concluding reports into structured scene sequences
for video reconstruction using Sora API.

Uses OpenAI GPT for parsing instead of Gemini.
"""

import json
import re
from typing import List, Dict, Any, Optional
from openai import OpenAI
import os

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class SceneParser:
    """
    Parses police reports into structured scene sequences for video generation.
    Uses OpenAI GPT to extract temporal events and map them to evidence images.
    """
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set.")
        
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"  # Cost-effective model for parsing
    
    def parse_report(
        self,
        report_text: str,
        num_images: int = 0,
        image_descriptions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Parse a police report into structured scene sequences.
        
        Args:
            report_text: The full police/concluding report text
            num_images: Number of evidence images available for scene mapping
            image_descriptions: Optional descriptions of each image for better mapping
            
        Returns:
            Dictionary containing:
                - scenes: List of scene objects with descriptions and image mappings
                - overall_setting: General setting description
                - timeline_summary: Brief timeline summary
        """
        
        image_context = ""
        if num_images > 0:
            image_context = f"\n\nNumber of evidence images available: {num_images}"
            if image_descriptions:
                image_context += "\nImage descriptions:\n"
                for i, desc in enumerate(image_descriptions):
                    image_context += f"  Image {i}: {desc}\n"
            else:
                image_context += "\nImages are numbered 0 to " + str(num_images - 1) + " in chronological order (beginning, middle, end of incident)."
        
        prompt = f"""You are a documentary filmmaker creating a visual reconstruction of the Isabella Stewart Gardner Museum. Create elegant, cinematic scene descriptions.

CRITICAL RULES - FOLLOW EXACTLY:
1. This is a HISTORICAL DOCUMENTARY about a museum and its art collection
2. Describe ONLY: museum architecture, galleries, paintings, sculptures, lighting, atmosphere
3. Use words like: "elegant", "historic", "Renaissance", "masterpiece", "gallery", "exhibition"
4. NEVER use: crime, theft, heist, stolen, suspect, investigation, evidence, security breach
5. Think of this as a PBS documentary showcasing beautiful art and architecture

Report context:
{report_text}
{image_context}

Output your response as a valid JSON object with this exact structure:
{{
    "overall_setting": "Historic art museum, elegant galleries, Renaissance masterpieces",
    "timeline_summary": "A visual tour of the museum's galleries and collection",
    "scenes": [
        {{
            "scene_number": 1,
            "timestamp": "Evening",
            "location": "Gallery name or museum area",
            "description": "Beautiful, artistic description of the museum space, architecture, and artwork. Focus on beauty, history, elegance. 2-3 sentences.",
            "key_elements": ["paintings", "frames", "gallery walls", "soft lighting", "marble floors"],
            "mood": "elegant, serene, historic, majestic",
            "associated_image_index": 0
        }}
    ]
}}

IMPORTANT: 
- Return ONLY valid JSON
- Create exactly 3 scenes (one per image)
- Describe the BEAUTY of art and architecture only
- NO references to anything negative or criminal"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a PBS documentary filmmaker creating elegant, artistic scene descriptions for a film about historic art museums and their collections. Focus purely on beauty, art, and architecture. Output valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            response_text = response.choices[0].message.content
            
            # Clean up response - remove markdown code blocks if present
            response_text = response_text.strip()
            if response_text.startswith("```"):
                # Remove markdown code block formatting
                response_text = re.sub(r'^```(?:json)?\s*', '', response_text)
                response_text = re.sub(r'\s*```$', '', response_text)
            
            # Parse JSON
            parsed = json.loads(response_text)
            
            # Validate structure
            if "scenes" not in parsed:
                parsed["scenes"] = []
            if "overall_setting" not in parsed:
                parsed["overall_setting"] = "Unknown setting"
            if "timeline_summary" not in parsed:
                parsed["timeline_summary"] = "Timeline not available"
            
            return parsed
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse LLM response as JSON: {e}")
            print(f"Raw response: {response_text[:500]}...")
            # Return a fallback structure
            return {
                "overall_setting": "Unable to parse report",
                "timeline_summary": "Parsing failed",
                "scenes": [],
                "error": str(e)
            }
        except Exception as e:
            print(f"Error in scene parsing: {e}")
            return {
                "overall_setting": "Error occurred",
                "timeline_summary": "Error occurred",
                "scenes": [],
                "error": str(e)
            }
    
    def generate_video_prompts(self, parsed_scenes: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convert parsed scenes into clean documentary prompts for Sora.
        Produces purely artistic, museum-focused descriptions.
        
        Args:
            parsed_scenes: Output from parse_report()
            
        Returns:
            List of dictionaries with 'prompt' and 'image_index' for each scene
        """
        # Words to completely remove from prompts
        banned_words = [
            'crime', 'criminal', 'theft', 'thief', 'steal', 'stolen', 'heist',
            'suspect', 'investigation', 'evidence', 'police', 'security breach',
            'break-in', 'intrusion', 'unauthorized', 'illegal', 'victim',
            'attack', 'assault', 'weapon', 'knife', 'gun', 'blood', 'injury',
            'dead', 'death', 'corpse', 'body', 'struggle', 'violence', 'threat',
            'forced entry', 'alarm', 'escape', 'fled', 'getaway', 'robbery'
        ]
        
        def clean_text(text: str) -> str:
            """Remove any problematic words entirely"""
            if not text:
                return text
            
            for word in banned_words:
                # Case-insensitive removal
                pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
                text = pattern.sub('', text)
            
            # Clean up extra spaces
            text = re.sub(r'\s+', ' ', text).strip()
            return text
        
        prompts = []
        
        for scene in parsed_scenes.get("scenes", []):
            # Build a pure art documentary prompt
            location = clean_text(scene.get('location', 'gallery'))
            description = clean_text(scene.get('description', ''))
            mood = scene.get('mood', 'elegant')
            
            # Make mood always positive/artistic
            mood_mapping = {
                'tense': 'dramatic',
                'chaotic': 'dynamic', 
                'urgent': 'cinematic',
                'dark': 'atmospheric',
                'suspicious': 'mysterious',
                'investigative': 'documentary'
            }
            mood = mood_mapping.get(mood.lower(), mood)
            
            # Construct clean documentary prompt
            scene_prompt = f"PBS art documentary. Historic museum interior. {location}. "
            scene_prompt += f"{description} "
            scene_prompt += f"Beautiful {mood} cinematography. "
            scene_prompt += "Soft natural lighting. Elegant composition. 4K quality."
            
            # Clean final prompt one more time
            scene_prompt = clean_text(scene_prompt)
            
            prompts.append({
                "scene_number": scene.get("scene_number", 0),
                "timestamp": scene.get("timestamp", ""),
                "prompt": scene_prompt.strip(),
                "image_index": scene.get("associated_image_index"),
                "mood": mood
            })
        
        return prompts


def parse_report_from_file(filepath: str, num_images: int = 0) -> Dict[str, Any]:
    """
    Convenience function to parse a report from a file path.
    
    Args:
        filepath: Path to the report text file
        num_images: Number of evidence images available
        
    Returns:
        Parsed scene structure
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        report_text = f.read()
    
    parser = SceneParser()
    return parser.parse_report(report_text, num_images)


if __name__ == "__main__":
    # Test with sample report
    import sys
    
    test_report_path = "footwear_rag/data/zip_files/message.txt"
    
    if len(sys.argv) > 1:
        test_report_path = sys.argv[1]
    
    print(f"🎬 Parsing report: {test_report_path}")
    print("=" * 60)
    
    try:
        result = parse_report_from_file(test_report_path, num_images=3)
        print(json.dumps(result, indent=2))
        
        print("\n" + "=" * 60)
        print("📽️ Generated Video Prompts:")
        print("=" * 60)
        
        parser = SceneParser()
        prompts = parser.generate_video_prompts(result)
        for p in prompts:
            print(f"\nScene {p['scene_number']} ({p['timestamp']}):")
            print(f"  Image Index: {p['image_index']}")
            print(f"  Prompt: {p['prompt'][:200]}...")
            
    except FileNotFoundError:
        print(f"❌ File not found: {test_report_path}")
    except Exception as e:
        print(f"❌ Error: {e}")
