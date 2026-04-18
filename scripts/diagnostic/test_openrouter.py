import os
import asyncio
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load from the backend .env
load_dotenv("backend/.env")

async def test_openrouter():
    api_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_MODEL", "minimax/minimax-m2.5:free")

    if not api_key:
        print("❌ ERROR: OPENROUTER_API_KEY not found in backend/.env")
        return

    print(f"🚀 Testing OpenRouter with model: {model}")
    print(f"🔑 Key prefix: {api_key[:8]}...")

    client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    try:
        print("📡 Sending test request (JSON Mode)...")
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a test assistant. Always output valid JSON."},
                {"role": "user", "content": "Say hello and return a JSON with a 'status' field."}
            ],
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        print(f"✅ Success! Raw Response: {content}")
        
        # Verify JSON
        parsed = json.loads(content)
        print(f"📦 Parsed Data: {parsed}")
        
    except Exception as e:
        print(f"❌ API Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_openrouter())
