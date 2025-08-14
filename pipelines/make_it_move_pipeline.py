#!/usr/bin/env python3
"""
Make It Move Pipeline
Connects image input -> Ollama Qwen description -> FramePack video generation
"""

import os
import base64
import requests
import json
from pathlib import Path
from typing import Optional, Dict, Any
import time


class MakeItMovePipeline:
    def __init__(self, 
                 ollama_host: str = "http://localhost:11434",
                 framepack_gradio_url: str = "http://127.0.0.1:7860",
                 qwen_model: str = "qwen2-vl"):
        """
        Initialize the pipeline
        
        Args:
            ollama_host: Ollama server URL
            framepack_gradio_url: FramePack Gradio interface URL
            qwen_model: Qwen model name in Ollama
        """
        self.ollama_host = ollama_host
        self.framepack_url = framepack_gradio_url
        self.qwen_model = qwen_model
        
    def encode_image_to_base64(self, image_path: str) -> str:
        """Encode image file to base64 string"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def generate_movement_description(self, image_path: str) -> str:
        """
        Use Ollama Qwen to analyze image and generate movement prompt
        """
        print(f"🔍 Analyzing image with Qwen: {image_path}")
        
        # Encode image
        image_b64 = self.encode_image_to_base64(image_path)
        
        # Craft prompt for movement generation
        prompt = """Analyze this image and create a detailed movement prompt for video generation. 

Focus on:
1. What objects/subjects are in the image that could move
2. Natural, realistic movements they might make
3. Environmental effects (wind, water, light changes)
4. Camera movements that would enhance the scene

Provide a concise but vivid movement description suitable for video generation. Be specific about direction, speed, and type of movement.

Format your response as a single paragraph movement prompt."""

        # Prepare request for Ollama
        payload = {
            "model": self.qwen_model,
            "prompt": prompt,
            "images": [image_b64],
            "stream": False
        }
        
        try:
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            movement_prompt = result.get('response', '').strip()
            
            print(f"✅ Generated movement prompt: {movement_prompt[:100]}...")
            return movement_prompt
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error calling Ollama: {e}")
            # Fallback prompt
            return "Gentle movement with natural lighting changes and subtle camera motion"
    
    def generate_video_via_gradio(self, image_path: str, movement_prompt: str) -> Optional[str]:
        """
        Call FramePack via Gradio API to generate video
        """
        print(f"🎬 Generating video with FramePack...")
        print(f"📝 Movement prompt: {movement_prompt}")
        
        try:
            # First, check if Gradio API is available
            response = requests.get(f"{self.framepack_url}/api/")
            response.raise_for_status()
            
            # Upload image file
            with open(image_path, 'rb') as f:
                files = {'file': f}
                upload_response = requests.post(
                    f"{self.framepack_url}/upload",
                    files=files
                )
            
            if upload_response.status_code != 200:
                print(f"❌ Failed to upload image: {upload_response.status_code}")
                return None
            
            # Get the uploaded file path/reference
            upload_result = upload_response.json()
            uploaded_file_ref = upload_result.get('file_path') or upload_result.get('name')
            
            # Prepare payload for video generation
            # Note: These parameters may need adjustment based on your FramePack setup
            payload = {
                "data": [
                    uploaded_file_ref,  # image input
                    movement_prompt,    # text prompt
                    "",                 # negative prompt (optional)
                    42,                 # seed
                    25,                 # num_inference_steps
                    7.5,                # guidance_scale
                    16,                 # num_frames
                    1024,               # width
                    576,                # height
                ]
            }
            
            # Call the prediction endpoint
            response = requests.post(
                f"{self.framepack_url}/api/predict",
                json=payload,
                timeout=300  # 5 minutes timeout for video generation
            )
            
            if response.status_code == 200:
                result = response.json()
                # Extract video file path from result
                video_path = result.get('data', [None])[0]
                
                if video_path:
                    print(f"✅ Video generated successfully: {video_path}")
                    return video_path
                else:
                    print("❌ No video path returned from FramePack")
                    return None
            else:
                print(f"❌ FramePack API error: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error generating video: {e}")
            return None
    
    def run_pipeline(self, image_path: str, output_dir: str = "./output") -> Optional[str]:
        """
        Run the complete pipeline: image -> description -> video
        
        Args:
            image_path: Path to input image
            output_dir: Directory to save output video
            
        Returns:
            Path to generated video file or None if failed
        """
        print(f"🚀 Starting Make It Move pipeline...")
        print(f"📸 Input image: {image_path}")
        
        # Validate input
        if not os.path.exists(image_path):
            print(f"❌ Image file not found: {image_path}")
            return None
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Step 1: Generate movement description
        movement_prompt = self.generate_movement_description(image_path)
        
        # Step 2: Generate video
        video_path = self.generate_video_via_gradio(image_path, movement_prompt)
        
        if video_path:
            # Copy/move video to output directory if needed
            output_path = os.path.join(output_dir, f"generated_video_{int(time.time())}.mp4")
            
            # If video_path is a URL, download it
            if video_path.startswith('http'):
                try:
                    video_response = requests.get(video_path)
                    video_response.raise_for_status()
                    with open(output_path, 'wb') as f:
                        f.write(video_response.content)
                    print(f"✅ Video saved to: {output_path}")
                    return output_path
                except Exception as e:
                    print(f"❌ Error downloading video: {e}")
                    return video_path  # Return original path
            else:
                # Local file path
                if os.path.exists(video_path):
                    # Could copy to output dir if desired
                    print(f"✅ Video available at: {video_path}")
                    return video_path
                else:
                    print(f"❌ Video file not found: {video_path}")
                    return None
        
        return None


def main():
    """CLI interface for the pipeline"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Make It Move - Image to Video Pipeline")
    parser.add_argument("image_path", help="Path to input image")
    parser.add_argument("--output-dir", default="./output", help="Output directory")
    parser.add_argument("--ollama-host", default="http://localhost:11434", help="Ollama server URL")
    parser.add_argument("--framepack-url", default="http://127.0.0.1:7860", help="FramePack Gradio URL")
    parser.add_argument("--qwen-model", default="qwen2-vl", help="Qwen model name")
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = MakeItMovePipeline(
        ollama_host=args.ollama_host,
        framepack_gradio_url=args.framepack_url,
        qwen_model=args.qwen_model
    )
    
    # Run pipeline
    result = pipeline.run_pipeline(args.image_path, args.output_dir)
    
    if result:
        print(f"\n🎉 Pipeline completed successfully!")
        print(f"📹 Generated video: {result}")
    else:
        print(f"\n❌ Pipeline failed")
        exit(1)


if __name__ == "__main__":
    main()

