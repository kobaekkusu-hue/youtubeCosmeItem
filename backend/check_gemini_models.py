import google.generativeai as genai
import os
import sys

def check_models(api_key):
    genai.configure(api_key=api_key)
    print(f"Checking models for key: ...{api_key[-6:]}")
    try:
        # モデル一覧の取得
        models = genai.list_models()
        model_names = [m.name for m in models]
        print("Available models:")
        for name in model_names:
            print(f" - {name}")
            
        target = "models/gemini-3-flash-preview"
        if target in model_names:
            print(f"✅ {target} is AVAILABLE.")
        else:
            # 部分一致チェック
            matches = [m for m in model_names if "3-flash" in m]
            if matches:
                 print(f"❓ Found similar models: {matches}")
            else:
                 print(f"❌ {target} is NOT found in the list.")
                 
    except Exception as e:
        print(f"Error checking models: {e}")

if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 else os.getenv("GEMINI_API_KEY")
    if not key:
        print("No API key provided.")
    else:
        check_models(key)
