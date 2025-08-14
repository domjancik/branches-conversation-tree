#!/usr/bin/env python3
"""
Simple test script to verify ollama connectivity for image prompt generation.
This script calls the get_image_prompts function to test if ollama is properly configured and accessible.
"""

import sys
import ollama
from image_prompt_generation import get_image_prompts

# Configure ollama client to use localhost
ollama_client = ollama.Client(host='http://localhost:11434')

def test_ollama_connectivity():
    """Test basic ollama connectivity by generating image prompts."""
    print("Testing ollama connectivity for image prompt generation...")
    print("-" * 50)
    
    # Test input text
    test_text = "A beautiful sunset over mountains with a lake"
    
    try:
        print(f"Input text: {test_text}")
        print("Calling ollama to generate image prompts...")
        
        # Call the function with a smaller prompt count for testing
        prompts = get_image_prompts(test_text, ollama_model="gemma2:2b", prompt_count=3)
        
        print(f"\n✅ Success! Generated {len(prompts)} image prompts:")
        for i, prompt in enumerate(prompts, 1):
            print(f"  {i}. {prompt}")
            
        print("\n🎉 Ollama connectivity test PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\n💡 Possible issues:")
        print("  - Ollama server is not running")
        print("  - Model 'gemma2:2b' is not installed")
        print("  - Network connectivity issues")
        print("  - Ollama configuration problems")
        print("\n🔧 Try running: ollama serve")
        print("🔧 Try installing model: ollama pull gemma2:2b")
        
        print("\n❌ Ollama connectivity test FAILED!")
        return False

def test_with_custom_model():
    """Test with a different model if available."""
    print("\n" + "="*50)
    print("Testing with alternative model...")
    
    test_text = "A simple test scene"
    alternative_models = ["llama3.1:8b", "llama3:8b", "llama2"]
    
    for model in alternative_models:
        try:
            print(f"\nTrying model: {model}")
            prompts = get_image_prompts(test_text, ollama_model=model, prompt_count=2)
            print(f"✅ Success with {model}!")
            for i, prompt in enumerate(prompts, 1):
                print(f"  {i}. {prompt}")
            return True
        except Exception as e:
            print(f"❌ Failed with {model}: {str(e)}")
            continue
    
    print("❌ No alternative models worked")
    return False

if __name__ == "__main__":
    print("🧪 Ollama Image Prompt Generation Test")
    print("=" * 50)
    
    # Test basic connectivity
    success = test_ollama_connectivity()
    
    # If primary test failed, try alternatives
    if not success:
        print("\nTrying alternative models...")
        test_with_custom_model()
    
    print("\n" + "=" * 50)
    print("Test completed!")
