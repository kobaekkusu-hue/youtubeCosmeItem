from yt_dlp import YoutubeDL
import json
import os

VIDEO_ID = '4fRgpzl9R-E'

def get_transcript_ytdlp(video_id):
    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['ja'],  # Japanese only
        'outtmpl': '%(id)s',
    }
    
    with YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            
            # Check requested subtitles
            subs = info.get('requested_subtitles')
            if not subs:
                 print("No subtitles found in metadata.")
                 # Try to force download anyway if keys exist in 'subtitles' or 'automatic_captions'
                 return
            
            ja_sub = subs.get('ja')
            if ja_sub:
                print(f"Found JA subtitle: {ja_sub.get('url')}")
                
                # Fetch content
                import requests
                res = requests.get(ja_sub['url'])
                print(f"Content Length: {len(res.text)}")
                print(res.text[:200])
            else:
                print("JA subtitle not in requested_subtitles.")

        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    get_transcript_ytdlp(VIDEO_ID)
