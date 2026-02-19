"""
商品画像を@cosmeやAmazon Japanの検索で取得し、DBに保存するスクリプト。

使い方:
  python fetch_product_images.py
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import requests
from bs4 import BeautifulSoup
from database import SessionLocal
from models import Product
import time
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
}

def search_cosme_image(product_name: str, brand: str = None) -> str | None:
    """@cosmeで商品画像を検索"""
    try:
        query = f"{brand} {product_name}" if brand else product_name
        # @cosme検索
        url = f"https://www.cosme.net/search/products?word={requests.utils.quote(query)}"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return None
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        # 商品画像を探す
        img = soup.select_one('img.p-cosme-product-list__image, img[data-src], .product-image img')
        if img:
            src = img.get('data-src') or img.get('src')
            if src and src.startswith('http'):
                return src
    except Exception as e:
        logger.warning(f"@cosme検索エラー: {e}")
    return None


def search_amazon_image(product_name: str, brand: str = None) -> str | None:
    """Amazon Japanで商品画像を検索"""
    try:
        query = f"{brand} {product_name}" if brand else product_name
        url = f"https://www.amazon.co.jp/s?k={requests.utils.quote(query)}"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return None
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Amazon検索結果の最初の商品画像
        img = soup.select_one('img.s-image')
        if img:
            src = img.get('src')
            if src and src.startswith('http'):
                return src
    except Exception as e:
        logger.warning(f"Amazon検索エラー: {e}")
    return None


def search_rakuten_image(product_name: str, brand: str = None) -> str | None:
    """楽天市場で商品画像を検索"""
    try:
        query = f"{brand} {product_name}" if brand else product_name
        url = f"https://search.rakuten.co.jp/search/mall/{requests.utils.quote(query)}/"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return None
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        # 楽天の商品画像
        img = soup.select_one('.dui-card__imageContainer img, .searchresultitem img')
        if img:
            src = img.get('src') or img.get('data-src')
            if src and src.startswith('http'):
                # 楽天の画像URLをクリーンアップ（リサイズパラメータ除去など）
                return src
    except Exception as e:
        logger.warning(f"楽天検索エラー: {e}")
    return None


def fetch_product_image(product_name: str, brand: str = None) -> str | None:
    """複数のソースから商品画像を探す"""
    # @cosme → Amazon → 楽天 の順で試行
    for searcher, name in [
        (search_cosme_image, "@cosme"),
        (search_amazon_image, "Amazon"),
        (search_rakuten_image, "楽天"),
    ]:
        logger.info(f"  {name}で検索中...")
        img_url = searcher(product_name, brand)
        if img_url:
            logger.info(f"  ✓ {name}で画像取得成功")
            return img_url
        time.sleep(1)  # レート制限対策
    return None


def main():
    db = SessionLocal()
    
    # 画像が未設定の商品を取得
    products = db.query(Product).filter(
        (Product.image_url == None) | (Product.image_url == '')
    ).all()
    
    logger.info(f"画像未設定の商品: {len(products)}件")
    
    updated = 0
    for i, product in enumerate(products, 1):
        logger.info(f"\n[{i}/{len(products)}] {product.name} ({product.brand})")
        
        img_url = fetch_product_image(product.name, product.brand)
        if img_url:
            product.image_url = img_url
            db.commit()
            updated += 1
            logger.info(f"  → 画像URL保存完了")
        else:
            logger.info(f"  → 画像が見つかりませんでした")
        
        time.sleep(2)  # サイト負荷軽減
    
    db.close()
    logger.info(f"\n=== 完了: {updated}/{len(products)}件の画像を更新 ===")


if __name__ == "__main__":
    main()
