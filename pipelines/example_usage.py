#!/usr/bin/env python3
"""
Example usage of the Make It Move pipeline
"""

from make_it_move_pipeline import MakeItMovePipeline
import os

def main():
    # Initialize the pipeline with your specific URLs
    pipeline = MakeItMovePipeline(
        ollama_host="http://localhost:11434",  # Your Ollama server
        framepack_gradio_url="http://127.0.0.1:7860",  # Your FramePack Gradio interface
        qwen_model="qwen2-vl"  # Your Qwen model name
    )
    
    # Example image path - replace with your actual image
    image_path = "path/to/your/image.jpg"
    
    # Check if example image exists
    if not os.path.exists(image_path):
        print("❌ Please update the image_path variable with a real image file")
        print("Example: image_path = r'C:\\Users\\magne\\Pictures\\my_image.jpg'")
        return
    
    # Run the pipeline
    print("🚀 Running Make It Move pipeline...")
    
    result = pipeline.run_pipeline(
        image_path=image_path,
        output_dir="./generated_videos"
    )
    
    if result:
        print(f"\n✅ Success! Generated video: {result}")
    else:
        print(f"\n❌ Pipeline failed")

if __name__ == "__main__":
    main()

