from fastapi import FastAPI, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db, engine, Base
from models import Product, Video, Review
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import datetime

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CosmeReview AI API")

# CORS
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
from fastapi.responses import JSONResponse
import traceback

# Middleware removed for debugging

# Pydantic Models for Response
class ReviewSchema(BaseModel):
    id: str
    video_id: str
    timestamp_seconds: int
    sentiment: Optional[str]
    summary: Optional[str]
    created_at: datetime.datetime
    video_title: Optional[str] = None
    video_thumbnail: Optional[str] = None
    channel_name: Optional[str] = None

    class Config:
        from_attributes = True

class VideoSchema(BaseModel):
    id: str
    title: str
    channel_name: Optional[str]
    published_at: Optional[datetime.datetime]
    thumbnail_url: Optional[str]
    
    @property
    def video_url(self):
        return f"https://www.youtube.com/watch?v={self.id}"

    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    id: str
    name: str
    brand: Optional[str]
    category: Optional[str]
    image_url: Optional[str]
    description: Optional[str] = None
    price: Optional[str] = None
    ingredients: Optional[str] = None
    volume: Optional[str] = None
    how_to_use: Optional[str] = None
    features: Optional[str] = None
    amazon_url: Optional[str] = None
    cosme_url: Optional[str] = None
    cosme_rating: Optional[float] = None

    class Config:
        from_attributes = True

class ProductSchema(ProductBase):
    review_count: int = 0
    positive_rate: float = 0.0

class ProductDetailSchema(ProductSchema):
    reviews: List[ReviewSchema] = []
    videos: List[VideoSchema] = []
    thumbnail_url: Optional[str] = None
    video_content_url: Optional[str] = None

@app.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    """カテゴリ一覧を取得"""
    categories = db.query(Product.category).distinct().all()
    return sorted([c[0] for c in categories if c[0]])

@app.get("/brands")
def get_brands(db: Session = Depends(get_db)):
    """ブランド一覧を取得"""
    brands = db.query(Product.brand).distinct().all()
    return sorted([b[0] for b in brands if b[0]])

@app.get("/products", response_model=List[ProductDetailSchema])
def get_products(
    q: Optional[str] = Query(None, description="Search query for product name, brand, or YouTuber"),
    category: Optional[str] = Query(None, description="Filter by category"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    skip: int = 0, 
    limit: int = 20, 
    db: Session = Depends(get_db)
):
    query = db.query(Product)
    
    # テキスト検索（商品名・ブランド・チャンネル名）
    if q:
        query = query.join(Review).join(Video).filter(
            Product.name.contains(q) | 
            Product.brand.contains(q) | 
            Video.channel_name.contains(q)
        ).distinct()
    
    # カテゴリフィルター
    if category:
        query = query.filter(Product.category == category)
    
    # ブランドフィルター
    if brand:
        query = query.filter(Product.brand == brand)

    products = query.offset(skip).limit(limit).all()
    print(f"Found {len(products)} products")
    
    results = []
    for product in products:
        product_data = ProductSchema.model_validate(product)
        
        # Get videos for this product
        # Get videos for this product via Reviews
        videos = db.query(Video).join(Review).filter(Review.product_id == product.id).distinct().all()
        video_data = [VideoSchema.model_validate(v) for v in videos]
        
        # Determine best video for thumbnail (first one or based on views if available)
        best_video = video_data[0] if video_data else None
        
        # Get reviews
        reviews = db.query(Review).filter(Review.product_id == product.id).all()
        review_data = [ReviewSchema.model_validate(r) for r in reviews]
        
        product_detail = ProductDetailSchema(
            **product_data.model_dump(exclude={'review_count', 'positive_rate'}),
            thumbnail_url=best_video.thumbnail_url if best_video else None,
            video_content_url=best_video.video_url if best_video else None,
            videos=video_data,
            reviews=review_data,
            review_count=len(reviews),
            positive_rate=round(sum([1 for r in reviews if r.sentiment == 'positive']) / len(reviews) * 100, 1) if reviews else 0
        )
        results.append(product_detail)
        
    # Return simple dict for now to debug
    return results

@app.get("/products/{product_id}", response_model=ProductDetailSchema)
def get_product_detail(product_id: str, db: Session = Depends(get_db)):
    print(f"DEBUG: get_product_detail called with product_id={product_id}")
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Populate review details with video info
    reviews_data = []
    for r in product.reviews:
        r_schema = ReviewSchema.model_validate(r)
        if r.video:
            r_schema.video_title = r.video.title
            r_schema.video_thumbnail = r.video.thumbnail_url
            r_schema.channel_name = r.video.channel_name
        reviews_data.append(r_schema)
    
    # Recalculate stats for detail view
    review_count = len(product.reviews)
    positive_reviews = [r for r in product.reviews if r.sentiment == 'positive']
    positive_rate = (len(positive_reviews) / review_count * 100) if review_count > 0 else 0
    
    p_base = ProductBase.model_validate(product)
    
    # Get videos via Review join (Product doesn't have direct videos relationship)
    videos = db.query(Video).join(Review).filter(Review.product_id == product.id).distinct().all()
    videos_data = [VideoSchema.model_validate(v) for v in videos]
    best_video = videos_data[0] if videos_data else None

    p_detail = ProductDetailSchema(
        **p_base.model_dump(),
        review_count=review_count,
        positive_rate=round(positive_rate, 1),
        reviews=reviews_data,
        videos=videos_data,
        thumbnail_url=best_video.thumbnail_url if best_video else None,
        video_content_url=best_video.video_url if best_video else None,
    )

    return p_detail
