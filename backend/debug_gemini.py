import os
from dotenv import load_dotenv
load_dotenv()
from services.youtube import YouTubeService
from services.gemini import GeminiService
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_video(video_id: str):
    yt = YouTubeService()
    gemini = GeminiService()
    
    logger.info(f"Fetching details for {video_id}...")
    details = yt.get_video_details(video_id)
    snippet = details['snippet']
    title = snippet['title']
    description = snippet['description']
    
    logger.info(f"Fetching transcript for {video_id}...")
    transcript = yt.get_transcript(video_id)
    if not transcript:
        logger.warning("No transcript found, using dummy.")
        transcript = [{"start": 0, "text": "（字幕なし）"}]
        
    logger.info(f"Analyzing with Gemini...")
    transcript_text = ""
    for item in transcript:
        start = int(item['start'])
        text = item['text']
        transcript_text += f"[{start}s] {text}\n"

    # Raw prompt test
    prompt = f"""以下のYouTube動画から、紹介されているコスメ商品を正確に抽出してください。
（中略）
【動画タイトル】
{title}
【概要欄】
{description[:2000]}
【字幕】
{transcript_text[:5000]}

出力形式: JSON配列のみ。
"""
    
    try:
        raw_text = gemini._generate_with_retry(prompt)
        logger.info(f"RAW RESPONSE FROM GEMINI:\n{raw_text}")
        
        # Parse it
        clean_text = raw_text
        if clean_text.startswith("```json"): clean_text = clean_text[7:]
        if clean_text.startswith("```"): clean_text = clean_text[3:]
        if clean_text.endswith("```"): clean_text = clean_text[:-3]
        
        data = json.loads(clean_text.strip())
        logger.info(f"PARSED DATA: {len(data)} items")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
    except Exception as e:
        logger.error(f"Debug failed: {e}")

if __name__ == "__main__":
    # 水越みさとの動画ID
    debug_video("numObkyIenI")
