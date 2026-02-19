from database import SessionLocal
from models import Video, Product, Review
import logging

logger = logging.getLogger(__name__)

def verify():
    db = SessionLocal()
    try:
        videos = db.query(Video).all()
        print(f"Total Videos: {len(videos)}")
        for v in videos:
            print(f"ID: {v.id}, Channel: {v.channel_name}, Date: {v.published_at}")
        
        products = db.query(Product).all()
        print(f"\nTotal Products: {len(products)}")
        for p in products[:5]:
            print(f"ID: {p.id[:8]}, Name: {p.name}")
            
        reviews = db.query(Review).all()
        print(f"\nTotal Reviews: {len(reviews)}")
        
    finally:
        db.close()

if __name__ == "__main__":
    verify()
