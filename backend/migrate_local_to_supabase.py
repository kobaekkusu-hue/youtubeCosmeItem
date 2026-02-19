import os
import sys
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from models import Base, Product, Video, Review

load_dotenv()

# --- 設定 ---
SQLITE_PATH = os.path.join(os.getcwd(), 'test.db')
POSTGRES_URL = os.getenv("DATABASE_URL")

if not POSTGRES_URL:
    print("Error: DATABASE_URL が設定されていません。")
    sys.exit(1)

print(f"DEBUG: SQLite  -> {SQLITE_PATH}")
print(f"DEBUG: Postgres -> {POSTGRES_URL[:20]}...")

# --- 接続の初期化 ---
sqlite_engine = create_engine(f"sqlite:///{SQLITE_PATH}")
pg_engine = create_engine(POSTGRES_URL)

SqliteSession = sessionmaker(bind=sqlite_engine)
PgSession = sessionmaker(bind=pg_engine)

def migrate():
    local_db = SqliteSession()
    cloud_db = PgSession()

    try:
        # 1. 既存データの削除 (外部キー制約を考慮)
        print("DEBUG: Supabase上の既存データを削除しています...")
        cloud_db.query(Review).delete()
        cloud_db.query(Product).delete()
        cloud_db.query(Video).delete()
        cloud_db.commit()

        # 2. Videos の移行
        print("DEBUG: Videos ユニットを抽出中...")
        videos = local_db.query(Video).all()
        print(f"DEBUG: {len(videos)} 件の動画データを移行中...")
        for v in videos:
            new_v = Video(
                id=v.id,
                title=v.title,
                channel_name=v.channel_name,
                published_at=v.published_at,
                thumbnail_url=v.thumbnail_url
            )
            cloud_db.add(new_v)
        cloud_db.flush()

        # 3. Products の移行
        print("DEBUG: Products ユニットを抽出中...")
        products = local_db.query(Product).all()
        print(f"DEBUG: {len(products)} 件の商品データを移行中...")
        for p in products:
            new_p = Product(
                id=p.id,
                name=p.name,
                brand=p.brand,
                category=p.category,
                image_url=p.image_url,
                description=p.description,
                price=p.price,
                ingredients=p.ingredients,
                volume=p.volume,
                how_to_use=p.how_to_use,
                features=p.features,
                amazon_url=p.amazon_url,
                cosme_url=p.cosme_url,
                cosme_rating=p.cosme_rating,
                created_at=p.created_at
            )
            cloud_db.add(new_p)
        cloud_db.flush()

        # 4. Reviews の移行
        print("DEBUG: Reviews ユニットを抽出中...")
        reviews = local_db.query(Review).all()
        print(f"DEBUG: {len(reviews)} 件のレビューデータを移行中...")
        for r in reviews:
            new_r = Review(
                id=r.id,
                product_id=r.product_id,
                video_id=r.video_id,
                timestamp_seconds=r.timestamp_seconds,
                sentiment=r.sentiment,
                summary=r.summary,
                created_at=r.created_at
            )
            cloud_db.add(new_r)
        
        # 5. 最終コミット
        cloud_db.commit()
        print("SUCCESS: 全データの移行が完了しました。")

    except Exception as e:
        print(f"ERROR: 移行中にエラーが発生しました: {e}")
        cloud_db.rollback()
    finally:
        local_db.close()
        cloud_db.close()

if __name__ == "__main__":
    migrate()
