# CogVideoX Image-to-Video Setup

## Overview

Switched from OpenAI Sora to **CogVideoX-5B-I2V** (open-source) because:
- ✅ **No content moderation** - works with crime scene/heist imagery
- ✅ **Open-source model** - fully free to use
- ✅ **Image-to-video support** - animates your evidence images
- ✅ **API-based** - no GPU required locally

## Setup Instructions

### 1. Get fal.ai API Key (FREE)

1. Go to: https://fal.ai/dashboard/keys
2. Sign up for a free account
3. Copy your API key
4. Add to `.env` file:

```env
FAL_KEY=your-fal-ai-key-here
OPENAI_API_KEY=your-openai-key  # Keep for scene parser (GPT-4)
GOOGLE_API_KEY=your-google-key   # Optional, not used anymore
```

### 2. Install Dependencies

Already installed:
```bash
pip install fal-client pillow
```

### 3. Test the System

Run the test script:
```bash
python test_cogvideo.py
```

This will:
1. Parse the Isabella Stewart Gardner Museum heist report
2. Extract 3-4 scenes
3. Generate videos for each scene using CogVideoX
4. Save videos to `outputs/videos/`

**Note:** Each video takes 2-5 minutes to generate via fal.ai API.

## How It Works

### Scene Parser (`scene_parser.py`)
- Uses OpenAI GPT-4o-mini to parse police reports
- Extracts chronological scenes with timestamps and descriptions
- Sanitizes prompts for art heist context (museum, gallery, investigation)
- Maps scenes to evidence images

### CogVideoX Service (`cogvideo_service.py`)
- Uploads your evidence images to fal.ai
- Calls CogVideoX-5B-I2V model via API
- Generates ~6 second video clips (8 fps)
- Downloads and saves videos locally

### Video Output
- **Duration:** ~6 seconds per scene
- **FPS:** 8 frames per second
- **Format:** MP4
- **Location:** `outputs/videos/scene_N_cogvideo.mp4`

## Pricing

fal.ai offers:
- **Free tier:** Limited credits per month
- **Pay-as-you-go:** $0.03 - $0.05 per video (approximately)
- Much cheaper than OpenAI Sora

Check current pricing: https://fal.ai/models/fal-ai/cogvideox-5b/image-to-video/api

## Troubleshooting

### "FAL_KEY not set"
Add your API key to the `.env` file in the project root.

### "fal_client not installed"
Run: `pip install fal-client`

### Videos not generating
- Check your fal.ai credit balance: https://fal.ai/dashboard
- Ensure images exist in `footwear_rag/data/zip_files/`
- Check API key is correct in `.env`

### "Queue position" messages
fal.ai uses a queue system. Your job will process when GPU becomes available.
This is normal and usually takes 2-5 minutes per video.

## Integration with Agent API

The `agent_api.py` can be updated to use CogVideoX instead of Sora:

```python
# In agent_api.py
from cogvideo_service import CogVideoService

# Replace SoraVideoService with CogVideoService
video_service = CogVideoService()

# Use the same interface
result = video_service.generate_reconstruction(
    scene_prompts=parsed_scenes,
    image_paths=image_list
)
```

## Advantages Over Sora

| Feature | Sora | CogVideoX |
|---------|------|-----------|
| Content Moderation | ❌ Very strict | ✅ Permissive |
| Heist/Crime Images | ❌ Blocked | ✅ Works |
| Pricing | $$$ Expensive | $ Affordable |
| Open Source | ❌ No | ✅ Yes |
| Organization Verification | ❌ Required | ✅ Not needed |
| Video Quality | Very high | Good |
| Video Length | 5-20s | ~6s |

## Alternative Models

If you want to try other open-source options:

1. **Replicate (CogVideoX)**
   - Same model, different provider
   - API: https://replicate.com/thudm/cogvideox-i2v

2. **Stable Video Diffusion**
   - Good quality, open-source
   - Requires more setup

3. **LTX-Video**
   - Higher quality
   - More expensive

## Support

- fal.ai docs: https://fal.ai/models/fal-ai/cogvideox-5b/image-to-video
- CogVideoX GitHub: https://github.com/THUDM/CogVideo
