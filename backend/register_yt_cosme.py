import json
import os
import datetime
import argparse
from urllib.parse import urlparse, parse_qs
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import Product, Video, Review

def get_video_id(url):
    """URLから動画IDを抽出する"""
    parsed = urlparse(url)
    if parsed.hostname in ('youtu.be', 'www.youtu.be'):
        return parsed.path[1:]
    if parsed.hostname in ('youtube.com', 'www.youtube.com'):
        return parse_qs(parsed.query).get('v', [None])[0]
    return None

def register_products():
    parser = argparse.ArgumentParser(description="抽出された商品情報をデータベースに登録する")
    parser.add_argument("--url", default="https://www.youtube.com/watch?v=uxMWQhk5YAo", help="商品が抽出された動画のURL")
    args = parser.parse_args()

    video_url = args.url
    video_id = get_video_id(video_url)
    
    if not video_id:
        print(f"Error: Could not extract video ID from {video_url}")
        return

    db = SessionLocal()
    
    # 抽出されたデータを読み込む
    input_file = "extracted_products.json"
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        products_data = json.load(f)

    # 動画情報の登録 (URLから抽出したIDを使用)
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        video = Video(
            id=video_id,
            title=f"YouTube Video ({video_id})", # タイトルは本来YouTube APIで取得すべきだが一旦ID化
            channel_name="YouTube Channel", 
            published_at=datetime.datetime.now(),
            thumbnail_url=f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        )
        db.add(video)
        db.commit()
        db.refresh(video)
        print(f"Registered video: {video.id}")

    # 商品情報の登録
    for item in products_data:
        # 同名の商品が既にあるかチェック
        product = db.query(Product).filter(Product.name == item["name"]).first()
        
        if not product:
            product = Product(
                name=item["name"],
                brand=item.get("brand"),
                category=item.get("category"),
                # descriptionは補完バッチ(enrich)で後ほど取得するため、ここでは埋めない
            )
            db.add(product)
            db.commit()
            db.refresh(product)
            print(f"Registered product: {product.name}")
        
        # 既にこの動画のレビューがあるかチェック
        review = db.query(Review).filter(Review.product_id == product.id, Review.video_id == video.id).first()
        if not review:
            review = Review(
                product_id=product.id,
                video_id=video.id,
                timestamp_seconds=item.get("timestamp_seconds", 0),
                sentiment="positive", # おすすめ動画なので positive とする
                summary=item.get("features") or "動画で紹介された商品です。",
                created_at=datetime.datetime.now()
            )
            db.add(review)
            db.commit()
            print(f"Added review for: {product.name} (at {review.timestamp_seconds}s)")

    db.close()
    print("Registration complete.")

if __name__ == "__main__":
    register_products()
