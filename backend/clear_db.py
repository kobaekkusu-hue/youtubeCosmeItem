from database import SessionLocal, engine
from models import Review, Product, Video, Base
from sqlalchemy import text
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_database():
    """
    データベースの全データを削除する（カスケード削除）。
    """
    db = SessionLocal()
    try:
        logger.info("データベースの全データを削除します...")
        
        # PostgreSQL (Supabase) 用のTRUNCATEコマンド
        # SQLiteの場合は動作が異なるため、dialectを確認
        if 'sqlite' in str(engine.url):
            logger.info("SQLite detected. Deleting rows individually.")
            db.query(Review).delete()
            db.query(Product).delete()
            db.query(Video).delete()
        else:
            logger.info("PostgreSQL detected. Using TRUNCATE CASCADE.")
            db.execute(text("TRUNCATE TABLE reviews, products, videos RESTART IDENTITY CASCADE"))
            
        db.commit()
        logger.info("✅ データベースの初期化が完了しました。")
        
    except Exception as e:
        logger.error(f"❌ データベースの初期化に失敗しました: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    #確認
    print("WARNING: This will delete ALL data in the database.")
    # 自動実行のため確認はスキップ（ユーザー指示済み）
    clear_database()
