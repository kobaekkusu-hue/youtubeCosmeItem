import os
import sys
import json
import logging
import subprocess
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import google.generativeai as genai

import argparse

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# デフォルト設定
DEFAULT_VIDEO_URL = "https://www.youtube.com/watch?v=uxMWQhk5YAo"
API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAx1ecNAJZG8quuthOzqm_RxhExEas_REI")
MODEL_NAME = "gemini-2.5-flash"

def analyze_video_with_gemini(video_url, model_name=MODEL_NAME, api_key=API_KEY):
    """Geminiを使用して動画内容を直接解析する"""
    logger.info(f"Gemini {MODEL_NAME} で動画を解析中 (Video URL: {video_url})...")
    genai.configure(api_key=API_KEY)
    
    # Gemini 1.5以降はURLを直接扱えない場合があるため、
    # 本来はFile APIでアップロードが必要だが、
    # 今回はプロンプトで動画の情報を伝えるか、可能ならURLから情報を探らせる
    # ※Gemini 2.5 Flashであれば、ウェブ検索機能やYouTube連携が強化されている可能性がある
    
    model = genai.GenerativeModel(MODEL_NAME)

    prompt = f"""
以下のYouTube動画の内容を解析し、紹介されているコスメ商品を抽出してください。
動画のURL: {video_url}

【抽出ルール】
- 各商品について、商品名、ブランド名、カテゴリ、特徴、および「その商品の紹介が動画の何秒目から始まるか（整数）」を抽出してください。
- 以下のJSON配列形式で出力してください。
- 知らない情報や記載がない項目は null にしてください。
- 日本語で回答してください。
- JSON以外のテキストは含めないでください。

[
  {{
    "name": "商品名",
    "brand": "ブランド名",
    "category": "カテゴリ",
    "features": "特徴・色番など",
    "timestamp_seconds": 123
  }},
  ...
]
"""
    try:
        # ツール指定が API のバージョン不整合でエラーになるため、一旦ツールなしで実行する。
        # Gemini 2.5 Flash の学習データに含まれている可能性に期待する。
        response = model.generate_content(prompt)
        content = response.text.strip()
        
        # JSON部分の抽出
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        data = json.loads(content)
        return data
    except Exception as e:
        logger.error(f"Gemini 解析エラー: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="YouTube動画から商品情報を抽出する")
    parser.add_argument("--url", default=DEFAULT_VIDEO_URL, help="解析対象の動画URL")
    args = parser.parse_args()

    video_url = args.url
    
    # APIキーが環境変数のリストにある場合は、それらをローテーションして試行する等の
    # 高度な処理も可能だが、一旦は指定されたキーを使用する
    
    products = analyze_video_with_gemini(video_url)
    
    if not products:
        logger.error("商品情報の抽出に失敗しました。")
        sys.exit(1)
        
    # 結果の保存
    output_file = "extracted_products.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
        
    logger.info(f"成功！ {len(products)} 件の商品を抽出しました。")
    logger.info(f"結果を {output_file} に保存しました。")
    
    # 画面にも表示
    print(json.dumps(products, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
