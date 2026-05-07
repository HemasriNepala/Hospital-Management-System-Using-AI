import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')

if not api_key:
    print("API_KEY_MISSING")
    exit()

genai.configure(api_key=api_key)
try:
    print("START_MODELS")
    for m in genai.list_models():
        print(f"NAME:{m.name}")
    print("END_MODELS")
except Exception as e:
    print(f"ERROR:{e}")
