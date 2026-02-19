import requests
try:
    response = requests.get("http://127.0.0.1:8000/products")
    print(f"Status Code: {response.status_code}")
    print("Response Body:")
    print(response.text)
except Exception as e:
    print(f"Request failed: {e}")
