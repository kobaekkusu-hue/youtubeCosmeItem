import sqlite3
import os
from database import SessionLocal, engine
from models import Video

def find_video_everywhere(video_id):
    print(f"Searching for video: {video_id}")
    
    # 1. Check Postgres (Supabase)
    db = SessionLocal()
    try:
        v = db.query(Video).filter(Video.id == video_id).first()
        print(f"Postgres (Supabase): {'FOUND' if v else 'NOT FOUND'}")
        if v:
            print(f"  - Title: {v.title}")
    except Exception as e:
        print(f"Postgres Error: {e}")
    finally:
        db.close()
    
    # 2. Check all .db files in current dir
    for f in os.listdir('.'):
        if f.endswith('.db'):
            try:
                conn = sqlite3.connect(f)
                cur = conn.cursor()
                # Check if table videos exists
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='videos'")
                if cur.fetchone():
                    cur.execute("SELECT id, title FROM videos WHERE id=?", (video_id,))
                    row = cur.fetchone()
                    print(f"File {f}: {'FOUND' if row else 'NOT FOUND'}")
                    if row:
                        print(f"  - Title: {row[1]}")
                conn.close()
            except Exception as e:
                print(f"File {f} Error: {e}")

if __name__ == "__main__":
    find_video_everywhere("numObkyIenI") # 水越みさと
    find_video_everywhere("PP2EjSqbTeA") # きぬ
