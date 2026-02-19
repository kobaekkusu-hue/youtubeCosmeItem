import uvicorn
# Import app from main.py
from main import app

if __name__ == "__main__":
    print("Starting Uvicorn programmatically...")
    try:
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="trace")
    except Exception as e:
        print(f"Uvicorn failed: {e}")
