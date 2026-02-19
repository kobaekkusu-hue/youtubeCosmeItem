from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import Product, Video, Review

# Ensure tables exist
Base.metadata.create_all(bind=engine)

def check_data():
    db = SessionLocal()
    try:
        product_count = db.query(Product).count()
        video_count = db.query(Video).count()
        review_count = db.query(Review).count()
        
        print(f"Products: {product_count}")
        print(f"Videos: {video_count}")
        print(f"Reviews: {review_count}")
        
        if product_count > 0:
            print("\n--- Sample Products ---")
            for p in db.query(Product).limit(5).all():
                print(f"- {p.name} ({p.brand})")
        
        if review_count > 0:
            print("\n--- Sample Reviews ---")
            for r in db.query(Review).limit(5).all():
                print(f"- {r.product.name}: {r.sentiment} ({r.summary[:30]}...)")
                
    except Exception as e:
        print(f"Error querying database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_data()
