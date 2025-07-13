#!/usr/bin/env python3
"""
Test script to verify OpenRouter configuration works correctly.
Run this script to test if your OpenRouter API key and base URL are working.
"""

import os
from openai import OpenAI

def test_openrouter():
    """Test OpenRouter API connection"""
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable is not set!")
        print("   Set it with: export OPENAI_API_KEY='your-openrouter-key'")
        return False
    
    print(f"🔑 API Key: {api_key[:10]}...{api_key[-4:]}")
    print(f"🌐 Base URL: {base_url}")
    
    try:
        # Create OpenAI client with OpenRouter base URL
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        # Test with a simple completion
        print("🧪 Testing API connection...")
        
        # Try different model names that are commonly available on OpenRouter
        models_to_try = [
            "o4-mini",  # The model used in AgentBeats
            "openai/gpt-4o-mini",  # Alternative name for o4-mini
            "openai/gpt-3.5-turbo",
            "anthropic/claude-3-haiku"
        ]
        
        success = False
        for model in models_to_try:
            try:
                print(f"   Trying model: {model}")
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "user", "content": "Say 'Hello from OpenRouter!' and nothing else."}
                    ],
                    max_tokens=50
                )
                result = response.choices[0].message.content
                print(f"✅ Success with model: {model}")
                print(f"✅ Response: {result}")
                success = True
                break
            except Exception as e:
                print(f"   ❌ Failed with {model}: {str(e)[:100]}...")
                continue
        
        if not success:
            raise Exception("All tested models failed. Check your OpenRouter account and available models.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure your OpenRouter API key is correct")
        print("2. Make sure OPENAI_API_BASE is set to 'https://openrouter.ai/api/v1'")
        print("3. Check your internet connection")
        print("4. Verify your OpenRouter account has credits")
        return False

if __name__ == "__main__":
    print("🚀 Testing OpenRouter Configuration")
    print("=" * 40)
    
    success = test_openrouter()
    
    if success:
        print("\n🎉 OpenRouter is configured correctly!")
        print("You can now run your AgentBeats services.")
    else:
        print("\n💡 Please fix the configuration and try again.")
        print("For help, see the README.md file.") 