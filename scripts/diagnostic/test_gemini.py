import os
import google.generativeai as genai
import asyncio
from dotenv import load_dotenv

load_dotenv("backend/.env")
api_key = os.getenv("GOOGLE_API_KEY")

async def test_api():
    if not api_key:
        print("No API key found")
        return
    
    print(f"Testing with key: {api_key[:5]}...{api_key[-5:]}")
    genai.configure(api_key=api_key)
    
    print("Available models:")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
    except Exception as e:
        print(f"Failed to list models: {e}")
    
    model_to_try = 'gemini-1.5-flash'
    print(f"Trying to use: {model_to_try}")
    model = genai.GenerativeModel(model_to_try)
    try:
        response = await model.generate_content_async("Say hello", generation_config={"response_mime_type": "application/json"})
        print(f"Success! Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_api())
