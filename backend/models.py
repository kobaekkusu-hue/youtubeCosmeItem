from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
import datetime
from database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, index=True)
    brand = Column(String, index=True)
    category = Column(String, index=True)
    image_url = Column(String)
    description = Column(Text, nullable=True)
    price = Column(String, nullable=True)
    ingredients = Column(Text, nullable=True)      # 成分表
    volume = Column(String, nullable=True)          # 容量（例: "30ml"）
    how_to_use = Column(Text, nullable=True)        # 使い方
    features = Column(Text, nullable=True)          # 特徴・ポイント（JSON配列文字列）
    amazon_url = Column(String, nullable=True)      # Amazon商品ページURL
    cosme_url = Column(String, nullable=True)       # @cosme商品ページURL
    cosme_rating = Column(Float, nullable=True)     # @cosmeの評価スコア
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    reviews = relationship("Review", back_populates="product")

class Video(Base):
    __tablename__ = "videos"

    id = Column(String, primary_key=True)  # YouTube Video ID
    title = Column(String)
    channel_name = Column(String)
    published_at = Column(DateTime)
    thumbnail_url = Column(String)

    reviews = relationship("Review", back_populates="video")

class Review(Base):
    __tablename__ = "reviews"

    id = Column(String, primary_key=True, default=generate_uuid)
    product_id = Column(String, ForeignKey("products.id"))
    video_id = Column(String, ForeignKey("videos.id"))
    timestamp_seconds = Column(Integer)
    sentiment = Column(String)  # positive, negative, neutral
    summary = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    product = relationship("Product", back_populates="reviews")
    video = relationship("Video", back_populates="reviews")
