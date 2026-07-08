"""Quick test script to verify Deepseek API configuration.

Run this script to test if Deepseek API is working correctly.

Usage:
    cd tests
    python test_deepseek_api.py
"""
import os
import sys
import io
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
BACKEND_ROOT = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

# Load environment variables from backend/.env
env_path = BACKEND_ROOT / ".env"
load_dotenv(env_path)

def test_deepseek_api():
    """Test Deepseek API connection and response."""
    print("=" * 60)
    print("Testing Deepseek API Configuration")
    print("=" * 60)

    # Check configuration
    provider = os.getenv("AI_PROVIDER")
    api_key = os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    model = os.getenv("AI_DEFAULT_MODEL", "deepseek-chat")

    print(f"\n📋 Configuration:")
    print(f"  Provider: {provider}")
    print(f"  Base URL: {base_url}")
    print(f"  Model: {model}")
    print(f"  API Key: {'*' * 20}{api_key[-8:] if api_key else 'MISSING'}")

    if not api_key or api_key.startswith("sk-your-deepseek"):
        print("\n❌ ERROR: DEEPSEEK_API_KEY not set properly!")
        print("   Please check your .env file.")
        return False

    try:
        import openai
    except ImportError:
        print("\n❌ ERROR: openai package not installed!")
        print("   Run: pip install openai")
        return False

    # Test API call
    print(f"\n🔍 Testing API call to {base_url}...")
    print("-" * 60)

    try:
        client = openai.OpenAI(api_key=api_key, base_url=base_url)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个友好的AI助手。"},
                {"role": "user", "content": "你好！请用一句话介绍你自己。"}
            ],
            max_tokens=100,
            timeout=30,
        )

        content = response.choices[0].message.content
        usage = response.usage

        print(f"\n✅ SUCCESS! API response received:")
        print(f"  Model: {response.model}")
        print(f"  Response: {content}")
        print(f"  Tokens: {usage.prompt_tokens} input, {usage.completion_tokens} output")

        print("\n" + "=" * 60)
        print("✨ Deepseek API is working correctly!")
        print("=" * 60)
        return True

    except openai.APITimeoutError as e:
        print(f"\n❌ TIMEOUT: Request timed out ({e})")
        print("   Check your network connection.")
        return False

    except openai.RateLimitError as e:
        print(f"\n❌ RATE LIMIT: {e}")
        print("   You may have exceeded your API quota.")
        return False

    except openai.AuthenticationError as e:
        print(f"\n❌ AUTH ERROR: {e}")
        print("   Check your DEEPSEEK_API_KEY in .env file.")
        return False

    except openai.APIError as e:
        print(f"\n❌ API ERROR: {e}")
        return False

    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        return False


def test_ai_provider_import():
    """Test importing AIProvider from chat_service."""
    print("\n" + "=" * 60)
    print("Testing AI Provider Import")
    print("=" * 60)

    try:
        from app.services.ai_provider import get_provider, reset_provider

        # Reset any existing provider
        reset_provider()

        # Get provider using config (should read from environment)
        provider_name = os.getenv("AI_PROVIDER", "openai")
        model = os.getenv("AI_DEFAULT_MODEL")
        base_url = os.getenv("DEEPSEEK_BASE_URL") if provider_name == "deepseek" else None

        provider = get_provider(
            provider=provider_name,  # type: ignore
            default_model=model,
            base_url=base_url,
        )

        print(f"\n✅ AIProvider imported successfully")
        print(f"  Provider: {provider.provider}")
        print(f"  Default Model: {provider.default_model}")
        print(f"  Base URL: {getattr(provider, 'base_url', 'N/A')}")

        return True
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🚀 Deepseek API Test Suite\n")

    # Test 1: Direct API call
    api_ok = test_deepseek_api()

    # Test 2: AI Provider import
    import_ok = test_ai_provider_import()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"  Direct API Call: {'✅ PASS' if api_ok else '❌ FAIL'}")
    print(f"  AI Provider:     {'✅ PASS' if import_ok else '❌ FAIL'}")
    print("=" * 60)

    if api_ok and import_ok:
        print("\n🎉 All tests passed! Deepseek is ready to use.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        sys.exit(1)
