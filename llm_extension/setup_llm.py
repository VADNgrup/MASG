"""
Setup Script for Pinkyne Extension

This script helps you setup and activate the Pinkyne extension.

Usage:
    python pinkyne_extension/setup_pinkyne.py
"""

import os
import sys
from pathlib import Path


def check_environment():
    """Check if environment is properly configured"""
    print("🔍 Checking environment...")
    print()
    
    # Check if .env exists
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  .env file not found")
        print("   Creating from .env.example...")
        
        env_example = Path(".env.example")
        if env_example.exists():
            import shutil
            shutil.copy(env_example, env_file)
            print("✅ Created .env file")
        else:
            print("❌ .env.example not found. Please create .env manually.")
            return False
    else:
        print("✅ .env file exists")
    
    # Check for API key
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("PINKYNE_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print()
        print("⚠️  API key not found in .env")
        print("   Please add one of the following to your .env file:")
        print("   - PINKYNE_API_KEY=your_api_key")
        print("   - OPENAI_API_KEY=your_api_key")
        return False
    else:
        print(f"✅ API key found: {'*' * 20}{api_key[-8:]}")
    
    print()
    return True


def test_imports():
    """Test if required packages are installed"""
    print("📦 Checking dependencies...")
    print()
    
    required = [
        ("openai", "OpenAI Python SDK"),
        ("langchain_openai", "LangChain OpenAI integration"),
        ("dotenv", "Python dotenv"),
    ]
    
    all_installed = True
    for module, name in required:
        try:
            __import__(module)
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name} not installed")
            all_installed = False
    
    print()
    
    if not all_installed:
        print("Please install missing packages:")
        print("  pip install -r requirements.txt")
        return False
    
    return True


def create_example_script():
    """Create an example usage script"""
    example_file = Path("example_pinkyne_usage.py")
    
    if example_file.exists():
        print(f"ℹ️  {example_file} already exists, skipping...")
        return
    
    content = '''"""
Example: Using Pinkyne Extension

This demonstrates how to use the Pinkyne extension in your scripts.
"""

# Step 1: Import pinkyne_extension FIRST (before any OpenAI imports)
import pinkyne_extension

# Step 2: Now import and use OpenAI as normal
from openai import OpenAI
from langchain_openai import ChatOpenAI

# These will automatically use Pinkyne API!

# Example 1: Direct OpenAI client
print("Example 1: Direct OpenAI Client")
client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "user", "content": "Say hello!"}
    ]
)
print(response.choices[0].message.content)
print()

# Example 2: LangChain
print("Example 2: LangChain ChatOpenAI")
llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
response = llm.invoke("What is 2+2?")
print(response.content)
print()

print("✅ All API calls went through Pinkyne!")
'''
    
    example_file.write_text(content)
    print(f"✅ Created {example_file}")
    print()


def update_main_py():
    """Suggest adding import to main.py"""
    main_file = Path("main.py")
    
    if not main_file.exists():
        print("ℹ️  main.py not found, skipping auto-update")
        return
    
    content = main_file.read_text()
    
    if "import pinkyne_extension" in content:
        print("✅ main.py already has pinkyne_extension import")
        return
    
    print("📝 To use Pinkyne in your main.py, add this line at the top:")
    print()
    print("    import pinkyne_extension")
    print()
    print("Do you want to add it automatically? (y/n): ", end="")
    
    try:
        choice = input().strip().lower()
        if choice == 'y':
            # Add import at the top, after docstring if any
            lines = content.split('\n')
            insert_pos = 0
            
            # Skip docstring
            if lines and lines[0].strip().startswith('"""'):
                for i, line in enumerate(lines):
                    if '"""' in line and i > 0:
                        insert_pos = i + 1
                        break
            
            lines.insert(insert_pos, "import pinkyne_extension  # Auto-added by setup_pinkyne.py")
            
            main_file.write_text('\n'.join(lines))
            print("✅ Added import to main.py")
        else:
            print("⏭️  Skipped")
    except:
        print("⏭️  Skipped")
    
    print()


def main():
    """Main setup function"""
    print("=" * 70)
    print("🚀 Pinkyne Extension Setup")
    print("=" * 70)
    print()
    
    # Check environment
    if not check_environment():
        print("❌ Environment check failed")
        sys.exit(1)
    
    # Check imports
    if not test_imports():
        print("❌ Dependency check failed")
        sys.exit(1)
    
    # Create example
    create_example_script()
    
    # Update main.py
    update_main_py()
    
    print("=" * 70)
    print("✅ Setup complete!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Run the test script to verify your API key:")
    print("   python -m pinkyne_extension.test_api")
    print()
    print("2. Use in your code by importing at the top:")
    print("   import pinkyne_extension")
    print()
    print("3. Check example_pinkyne_usage.py for examples")
    print()


if __name__ == "__main__":
    main()
