import google.generativeai as genai
import sys

def test_minimal_request(api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-3-flash-preview")
    print(f"Testing gemini-3-flash-preview with key ...{api_key[-6:]}")
    try:
        response = model.generate_content("Hi")
        print(f"Success! Response: {response.text}")
    except Exception as e:
        print(f"Error during minimal request: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_minimal_request(sys.argv[1])
    else:
        print("No API key provided.")
