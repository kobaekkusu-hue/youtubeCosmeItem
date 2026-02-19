import requests
import re
import json

VIDEO_ID = '4fRgpzl9R-E'
URL = f"https://www.youtube.com/watch?v={VIDEO_ID}"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

print(f"Fetching {URL}...")
response = requests.get(URL, headers=headers)
print(f"Status: {response.status_code}")

if "captionTracks" in response.text:
    print("Success! Found captionTracks.")
    match = re.search(r'"captionTracks":(\[.*?\])', response.text)
    if match:
        data = json.loads(match.group(1))
        print(f"Found {len(data)} tracks.")
        for track in data:
            print(f"- {track['name']['simpleText']} ({track['languageCode']})")
            if track['languageCode'] == 'ja':
                print(f"  URL: {track['baseUrl']}")
else:
    print("Failed to find captionTracks via requests.")
