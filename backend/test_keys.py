import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def test_keys():
    keys = [os.getenv(f"GEMINI_API_KEY_{i}") for i in range(1, 11) if os.getenv(f"GEMINI_API_KEY_{i}")]
    if os.getenv("GEMINI_API_KEY"):
        keys.insert(0, os.getenv("GEMINI_API_KEY"))
    
    model_name = 'gemini-2.5-flash'
    
    print(f"Testing {len(keys)} keys...")
    for i, k in enumerate(keys):
        genai.configure(api_key=k)
        try:
            # モデルのリストを取得してモデルの存在を確認
            models = genai.list_models()
            found = False
            for m in models:
                if model_name in m.name:
                    found = True
                    break
            
            if not found:
                 print(f"Key {i}: FAILED - Model {model_name} not found")
                 continue

            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Hi")
            print(f"Key {i}: WORKING - Response: {response.text.strip()}")
        except Exception as e:
            print(f"Key {i}: FAILED - {str(e)[:150]}")

if __name__ == "__main__":
    test_keys()
