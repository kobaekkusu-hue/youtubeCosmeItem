from database import SessionLocal
from models import Product

def check():
    db = SessionLocal()
    targets = ['Wデーション', 'スリムシャープアイライナー', 'クリームチーク パールタイプ', 'THE アイパレ', 'デューイアップ']
    for t in targets:
        p = db.query(Product).filter(Product.name.like(f'%{t}%')).first()
        if p:
            print(f"Name: {p.name}")
            print(f"  Ingredients: {'Yes' if p.ingredients else 'No'}")
            print(f"  How to use: {'Yes' if p.how_to_use else 'No'}")
            print(f"  Desc Len: {len(p.description) if p.description else 0}")
        else:
            print(f"Not found: {t}")
    db.close()

if __name__ == "__main__":
    check()
