from database import SessionLocal
from models import Product, Review, Video
import uuid
import datetime

def test_supabase_connection():
    print("DEBUG: Supabase 接続テスト開始...")
    db = SessionLocal()
    try:
        # 1. 保存テスト
        # まず Video を作成
        video_id = f"vid-{uuid.uuid4().hex[:8]}"
        new_video = Video(
            id=video_id,
            title="テスト動画",
            channel_name="テストチャンネル",
            published_at=datetime.datetime.utcnow(),
            thumbnail_url="https://example.com/thumb.jpg"
        )
        db.add(new_video)
        
        # 次に Product を作成
        dummy_id = f"test-{uuid.uuid4().hex[:8]}"
        new_product = Product(
            id=dummy_id,
            name="テスト商品",
            brand="テストブランド",
            category="スキンケア",
            description="Supabase 連携テスト用のデータです。",
            cosme_rating=4.5
        )
        db.add(new_product)
        
        # Review を作成
        new_review = Review(
            id=f"rev-{uuid.uuid4().hex[:8]}",
            product_id=dummy_id,
            video_id=video_id,
            sentiment="positive",
            summary="とても良いです。",
            timestamp_seconds=120
        )
        db.add(new_review)
        
        db.commit()
        print(f"DEBUG: データ保存成功 (ID: {dummy_id})")

        # 2. 取得テスト
        product = db.query(Product).filter(Product.id == dummy_id).first()
        if product:
            print(f"DEBUG: データ取得成功: {product.name}")
            print(f"DEBUG: 関連レビュー数: {len(product.reviews)}")
            if len(product.reviews) > 0:
                print(f"DEBUG: 関連動画タイトル: {product.reviews[0].video.title}")
        
    except Exception as e:
        print(f"ERROR: Supabase 連携エラー: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_supabase_connection()
