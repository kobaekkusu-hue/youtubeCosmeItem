import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
print(f"Using API Key: ...{api_key[-6:]}")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

try:
    response = model.generate_content("Hi. Reply with 'OK'.")
    print(f"Response: {response.text.strip()}")
except Exception as e:
    print(f"Error: {e}")
