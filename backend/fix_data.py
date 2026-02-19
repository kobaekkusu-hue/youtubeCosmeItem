from database import SessionLocal
from models import Product
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_product_names():
    db = SessionLocal()
    try:
        # 文字化けと対応のマップ
        # 以前の出力から推測される文字化けパターン
        mappings = [
            ("Wf[V", "Wデーション"),
            ("XV[vACCi[", "スリムシャープアイライナー"),
            ("N[[N p[^Cv", "クリームチーク パールタイプ"),
            ("THE ACp", "THE アイパレ"),
            ("W f[CAbvACpbg", "W デューイアップアイパレット"),
            ("Anua r^~10", "Anua ビタC"), # 推測
            ("C~v", "シャープ"), # 推測
            ("C~", "シャープ"), # 推測
        ]

        products = db.query(Product).all()
        for p in products:
            original_name = p.name
            new_name = original_name
            
            # 特殊な文字化けパターンを置換
            if "Wf[V" in original_name:
                new_name = original_name.replace("Wf[V", "Wデーション")
            elif "XV[v" in original_name:
                new_name = original_name.replace("XV[v", "スリムシャープ")
            elif "ACCi[" in original_name:
                new_name = original_name.replace("ACCi[", "アイライナー")
            elif "N[[N" in original_name:
                new_name = original_name.replace("N[[N", "クリーム")
            elif "p[^Cv" in original_name:
                new_name = original_name.replace("p[^Cv", "パールタイプ")
            elif "THE ACp" in original_name:
                new_name = original_name.replace("THE ACp", "THE アイパレ")
            elif "W f[CA" in original_name:
                new_name = original_name.replace("W f[CA", "W デューイアップ")
            elif "vACpbg" in original_name:
                new_name = original_name.replace("vACpbg", "アイパレット")
            
            # もし名前が変わった場合、または image_url が None の場合、
            # image_url をリセットして再取得を促す
            if original_name != new_name:
                logger.info(f"Fixing name: {original_name} -> {new_name}")
                p.name = new_name
                p.image_url = None # 再取得させる
            
            if not p.image_url:
                logger.info(f"Image missing for: {p.name}, will re-enrich.")

        db.commit()
    except Exception as e:
        logger.error(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_product_names()
