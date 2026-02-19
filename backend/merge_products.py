"""
既存の重複商品を名寄せ（マージ）するワンショットスクリプト。

処理内容:
1. 全商品の名前を正規化してグループ化
2. 重複グループ内の最古のレコードを「正規」として残す
3. 重複レコードの Review を正規レコードに移動
4. 不要な重複レコードを削除
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from database import SessionLocal
from models import Product, Review
from batch_processor import normalize_name
from collections import defaultdict

def merge_products():
    db = SessionLocal()
    
    # 全商品を取得
    all_products = db.query(Product).all()
    print(f"全商品数: {len(all_products)}")
    
    # 正規化名でグループ化
    groups = defaultdict(list)
    for product in all_products:
        normalized = normalize_name(product.name)
        groups[normalized].append(product)
    
    # 重複グループを特定
    duplicates = {k: v for k, v in groups.items() if len(v) > 1}
    print(f"重複グループ数: {len(duplicates)}")
    
    if not duplicates:
        print("重複はありません。処理を終了します。")
        db.close()
        return
    
    merged_count = 0
    for normalized_name, products in duplicates.items():
        # 最古のレコードを正規とする（created_at でソート）
        products.sort(key=lambda p: p.created_at or "")
        canonical = products[0]
        duplicates_to_remove = products[1:]
        
        print(f"\n--- 重複グループ: '{normalized_name}' ---")
        print(f"  正規レコード: '{canonical.name}' (ID: {canonical.id[:8]}..., ブランド: {canonical.brand})")
        
        for dup in duplicates_to_remove:
            print(f"  重複レコード: '{dup.name}' (ID: {dup.id[:8]}..., ブランド: {dup.brand})")
            
            # 重複レコードの Review を正規レコードに移動
            reviews = db.query(Review).filter(Review.product_id == dup.id).all()
            for review in reviews:
                review.product_id = canonical.id
                print(f"    Review {review.id[:8]}... を移動")
            
            # 重複レコードを削除
            db.delete(dup)
            merged_count += 1
    
    db.commit()
    db.close()
    
    # 結果表示
    remaining = db.query(Product).count() if False else len(all_products) - merged_count
    print(f"\n=== マージ完了 ===")
    print(f"削除された重複: {merged_count}")
    print(f"残り商品数: {remaining}")

if __name__ == "__main__":
    merge_products()
