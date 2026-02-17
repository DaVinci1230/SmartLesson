"""Quick script to check available Gemini models"""
import google.genai as genai
import os

api_key = os.getenv('GEMINI_API_KEY', 'test-key')
client = genai.Client(api_key=api_key)

print("Available Gemini models:")
try:
    models = client.models.list()
    for model in models:
        print(f"  - {model.name}")
        if hasattr(model, 'supported_generation_methods'):
            print(f"    Methods: {model.supported_generation_methods}")
except Exception as e:
    print(f"Error: {e}")
