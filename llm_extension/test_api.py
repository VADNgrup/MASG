"""
Pinkyne API Test Script

This script tests the Pinkyne API endpoints to ensure:
1. API key is valid and working
2. Chat completions endpoint works
3. Image generation endpoint works  
4. Vision API (image analysis) works

Usage:
    python -m pinkyne_extension.test_api
    
    # Or with verbose output:
    PINKYNE_VERBOSE=true python -m pinkyne_extension.test_api
"""

import os
import sys
from pathlib import Path
import asyncio
import base64
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pinkyne_extension.pinkyne_client import PinkyneClient
from pinkyne_extension.pinkyne_langchain import ChatPinkyne
from pinkyne_extension.pinkyne_config import pinkyne_config


class PinkyneAPITester:
    """Test suite for Pinkyne API"""
    
    def __init__(self):
        self.client = None
        self.chat_client = None
        self.results = {}
        self.errors = []
    
    def setup(self):
        """Initialize clients"""
        print("=" * 70)
        print("🧪 Pinkyne API Test Suite")
        print("=" * 70)
        print()
        
        try:
            pinkyne_config.validate()
            print(f"✅ Configuration valid")
            print(f"   Base URL: {pinkyne_config.BASE_URL}")
            print(f"   API Key: {'*' * 20}{pinkyne_config.API_KEY[-8:] if pinkyne_config.API_KEY else 'NOT SET'}")
            print()
        except ValueError as e:
            print(f"❌ Configuration error: {e}")
            sys.exit(1)
        
        self.client = PinkyneClient()
        self.chat_client = ChatPinkyne(model="gpt-4o", temperature=0.1)
        print("✅ Clients initialized")
        print()
    
    def test_simple_chat_completion(self) -> bool:
        """Test 1: Simple chat completion"""
        print("-" * 70)
        print("Test 1: Simple Chat Completion")
        print("-" * 70)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "The capital of France is ?"}
                ],
                max_tokens=50,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            print(f"✅ Chat completion successful")
            print(f"   Model: {response.model}")
            print(f"   Response: {result}")
            print(f"   Tokens used: {response.usage.total_tokens}")
            print()
            
            self.results['simple_chat'] = {
                'status': 'success',
                'response': result,
                'tokens': response.usage.total_tokens
            }
            return True
            
        except Exception as e:
            print(f"❌ Chat completion failed: {e}")
            print()
            self.errors.append(('simple_chat', str(e)))
            self.results['simple_chat'] = {'status': 'failed', 'error': str(e)}
            return False
    
    def test_langchain_chat(self) -> bool:
        """Test 2: LangChain ChatPinkyne"""
        print("-" * 70)
        print("Test 2: LangChain ChatPinkyne")
        print("-" * 70)
        
        try:
            response = self.chat_client.invoke("What is 2+2? Answer with just the number.")
            
            result = response.content.strip()
            print(f"✅ LangChain chat successful")
            print(f"   Response: {result}")
            print()
            
            self.results['langchain_chat'] = {
                'status': 'success',
                'response': result
            }
            return True
            
        except Exception as e:
            print(f"❌ LangChain chat failed: {e}")
            print()
            self.errors.append(('langchain_chat', str(e)))
            self.results['langchain_chat'] = {'status': 'failed', 'error': str(e)}
            return False
    
    def test_vision_api(self) -> bool:
        """Test 3: Vision API (image analysis)"""
        print("-" * 70)
        print("Test 3: Vision API (Image Analysis)")
        print("-" * 70)
        
        try:
            # Create a simple test image (1x1 red pixel)
            import base64
            from io import BytesIO
            from PIL import Image
            
            # Create a small test image
            img = Image.new('RGB', (100, 100), color='red')
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "What color is this image? Answer with just the color name."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=50
            )
            
            result = response.choices[0].message.content.strip()
            print(f"✅ Vision API successful")
            print(f"   Response: {result}")
            print()
            
            self.results['vision_api'] = {
                'status': 'success',
                'response': result
            }
            return True
            
        except Exception as e:
            print(f"❌ Vision API failed: {e}")
            print()
            self.errors.append(('vision_api', str(e)))
            self.results['vision_api'] = {'status': 'failed', 'error': str(e)}
            return False
    
    def test_image_generation(self) -> bool:
        """Test 4: Image generation (DALL-E)"""
        print("-" * 70)
        print("Test 4: Image Generation (DALL-E)")
        print("-" * 70)
        
        try:
            response = self.client.images.generate(
                model="dall-e-3",
                prompt="A simple red circle on white background",
                size="1024x1024",
                quality="standard",
                n=1
            )
            
            image_url = response.data[0].url
            print(f"✅ Image generation successful")
            print(f"   Image URL: {image_url[:80]}...")
            print(f"   Revised prompt: {response.data[0].revised_prompt[:100]}...")
            print()
            
            self.results['image_generation'] = {
                'status': 'success',
                'url': image_url
            }
            return True
            
        except Exception as e:
            print(f"❌ Image generation failed: {e}")
            print()
            self.errors.append(('image_generation', str(e)))
            self.results['image_generation'] = {'status': 'failed', 'error': str(e)}
            return False
    
    def test_structured_output(self) -> bool:
        """Test 5: Structured JSON output"""
        print("-" * 70)
        print("Test 5: Structured JSON Output")
        print("-" * 70)
        
        try:
            import json
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": 'Return a JSON object with fields "status": "ok" and "value": 42. Return ONLY valid JSON.'
                    }
                ],
                max_tokens=100,
                temperature=0.0
            )
            
            result = response.choices[0].message.content.strip()
            
            # Try to parse as JSON
            if result.startswith("```json"):
                result = result.split("```json")[1].split("```")[0].strip()
            elif result.startswith("```"):
                result = result.split("```")[1].split("```")[0].strip()
            
            parsed = json.loads(result)
            
            print(f"✅ Structured output successful")
            print(f"   Response: {result}")
            print(f"   Parsed: {parsed}")
            print()
            
            self.results['structured_output'] = {
                'status': 'success',
                'response': parsed
            }
            return True
            
        except Exception as e:
            print(f"❌ Structured output failed: {e}")
            print()
            self.errors.append(('structured_output', str(e)))
            self.results['structured_output'] = {'status': 'failed', 'error': str(e)}
            return False
    
    def print_summary(self):
        """Print test summary"""
        print("=" * 70)
        print("📊 Test Summary")
        print("=" * 70)
        print()
        
        total = len(self.results)
        passed = sum(1 for r in self.results.values() if r['status'] == 'success')
        failed = total - passed
        
        print(f"Total tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print()
        
        if self.errors:
            print("Errors:")
            for test_name, error in self.errors:
                print(f"  - {test_name}: {error}")
            print()
        
        if passed == total:
            print("🎉 All tests passed! Your Pinkyne API key is working correctly.")
        elif passed > 0:
            print("⚠️  Some tests passed. Check errors above.")
        else:
            print("❌ All tests failed. Please check your API key and configuration.")
        
        print()
        print("=" * 70)
    
    def run_all_tests(self):
        """Run all tests"""
        self.setup()
        
        # Run tests
        tests = [
            self.test_simple_chat_completion,
            self.test_langchain_chat,
            self.test_vision_api,
            self.test_image_generation,
            self.test_structured_output,
        ]
        
        for test in tests:
            try:
                test()
            except KeyboardInterrupt:
                print("\n⚠️  Tests interrupted by user")
                break
            except Exception as e:
                print(f"❌ Unexpected error in {test.__name__}: {e}")
                self.errors.append((test.__name__, str(e)))
        
        self.print_summary()
        
        # Return exit code
        return 0 if not self.errors else 1


def main():
    """Main entry point"""
    tester = PinkyneAPITester()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
