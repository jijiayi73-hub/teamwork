"""火山引擎豆包文生图最小验证脚本。

使用方式:
1. 配置 backend/.env 中的 VOLCES_API_KEY
2. 运行: py scripts/test_volces_image.py
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Get API key
api_key = os.getenv("VOLCES_API_KEY") or os.getenv("ARK_API_KEY")
base_url = os.getenv("VOLCES_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
model = os.getenv("VOLCES_IMAGE_MODEL", "doubao-seedream-5-0-260128")

print("=" * 50)
print("Volces Ark Image Generation - Minimal Test")
print("=" * 50)
print(f"Base URL: {base_url}")
print(f"Model: {model}")

if not api_key or api_key == "your-volces-api-key-here":
    print("\n[ERROR] VOLCES_API_KEY not configured")
    print("\nPlease set in backend/.env:")
    print("VOLCES_API_KEY=your-actual-api-key-here")
    print("\nOr:")
    print("ARK_API_KEY=your-actual-api-key-here")
    sys.exit(1)

print(f"API Key: {api_key[:8]}...{api_key[-4:]}")

try:
    print("\n[INFO] Initializing OpenAI client...")
    client = OpenAI(
        base_url=base_url,
        api_key=api_key,
    )

    print("[OK] Client initialized successfully")

    # Test prompt
    prompt = "A cute orange cat sitting on a windowsill, sunlight on its fur, warm and healing style"

    print(f"\n[PROMPT] {prompt}")
    print("[INFO] Calling Volces Ark API...")

    response = client.images.generate(
        model=model,
        prompt=prompt,
        size="2K",
        response_format="url",
        extra_body={
            "watermark": False,
        },
    )

    print("[OK] API call successful!")
    print(f"\nImage URL: {response.data[0].url}")
    print(f"\nTip: Copy URL to browser to view the generated image")

    # Show response details
    result = response.data[0]
    print("\n" + "=" * 50)
    print("Response Details:")
    print("=" * 50)
    print(f"Image URL: {result.url}")
    if hasattr(result, 'revised_prompt'):
        print(f"Revised Prompt: {result.revised_prompt}")

    print("\n[SUCCESS] Verification complete! Volces Ark image generation is working")

except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}")
    print(f"   {e}")
    print("\nPossible reasons:")
    print("1. API Key is incorrect or expired")
    print("2. Network connection issue")
    print("3. API quota exceeded")
    print("4. Model name incorrect")
    sys.exit(1)
