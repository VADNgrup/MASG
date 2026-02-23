"""
Quick Start Guide - Pinkyne Extension

Hướng dẫn nhanh để bắt đầu sử dụng Pinkyne API trong dự án LecSlideGen.
"""

# IMPORTANT: Import pinkyne_extension FIRST, before any OpenAI imports!
import pinkyne_extension

# Now you can import and use OpenAI/LangChain normally
from openai import OpenAI
from langchain_openai import ChatOpenAI

def example_1_simple_chat():
    """Example 1: Simple chat completion"""
    print("=" * 60)
    print("Example 1: Simple Chat Completion")
    print("=" * 60)
    
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello in Vietnamese!"}
        ],
        max_tokens=100
    )
    
    print(f"Response: {response.choices[0].message.content}")
    print(f"Tokens used: {response.usage.total_tokens}")
    print()


def example_2_langchain():
    """Example 2: Using LangChain"""
    print("=" * 60)
    print("Example 2: LangChain Integration")
    print("=" * 60)
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
    response = llm.invoke("Explain what is machine learning in one sentence.")
    
    print(f"Response: {response.content}")
    print()


def example_3_vision():
    """Example 3: Vision API"""
    print("=" * 60)
    print("Example 3: Vision API (Image Analysis)")
    print("=" * 60)
    
    import base64
    from io import BytesIO
    from PIL import Image
    
    # Create a test image
    img = Image.new('RGB', (100, 100), color='blue')
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What color is this image?"},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{img_base64}"}
                    }
                ]
            }
        ],
        max_tokens=50
    )
    
    print(f"Response: {response.choices[0].message.content}")
    print()


def example_4_check_config():
    """Example 4: Check configuration"""
    print("=" * 60)
    print("Example 4: Configuration Check")
    print("=" * 60)
    
    from pinkyne_extension import pinkyne_config
    
    print(f"Base URL: {pinkyne_config.BASE_URL}")
    print(f"API Key set: {bool(pinkyne_config.API_KEY)}")
    print(f"Verbose mode: {pinkyne_config.VERBOSE}")
    print()


def main():
    """Run all examples"""
    print("\n")
    print("🚀 Pinkyne Extension - Quick Start Examples")
    print("=" * 60)
    print()
    
    try:
        example_1_simple_chat()
        example_2_langchain()
        example_3_vision()
        example_4_check_config()
        
        print("=" * 60)
        print("✅ All examples completed successfully!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Check README.md for detailed documentation")
        print("2. Run test suite: python -m pinkyne_extension.test_api")
        print("3. Start using in your project by adding:")
        print("   import pinkyne_extension")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nPlease check:")
        print("1. API key is set in .env file")
        print("2. Dependencies are installed")
        print("3. Pinkyne API is accessible")


if __name__ == "__main__":
    main()
