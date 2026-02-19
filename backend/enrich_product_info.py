"""
Gemini AIを使って商品の詳細情報を生成・充実させるスクリプト。

Amazon/@cosmeのスクレイピングはbot検出でブロックされることがあるため、
Geminiのコスメ知識を活用して商品説明・特徴・成分・使い方を生成する。

使い方:
  python enrich_product_info.py
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import json
import time
import logging
import requests
from bs4 import BeautifulSoup
from database import SessionLocal
from models import Product
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Gemini設定
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)
else:
    logger.error("GEMINI_API_KEY が未設定です。.env ファイルを確認してください。")
    sys.exit(1)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
}


def fetch_amazon_url_and_price(product_name: str, brand: str = None) -> dict:
    """Amazon検索結果からURLと価格だけ取得（軽量版）"""
    info = {}
    try:
        query = f"{brand} {product_name}" if brand else product_name
        url = f"https://www.amazon.co.jp/s?k={requests.utils.quote(query)}"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return info
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        first = soup.select_one('[data-component-type="s-search-result"]')
        if not first:
            return info
        
        link = first.select_one('h2 a')
        if link:
            href = link.get('href', '')
            info['amazon_url'] = ('https://www.amazon.co.jp' + href).split('/ref=')[0]
        
        price_el = first.select_one('.a-price .a-offscreen')
        if price_el:
            info['price'] = price_el.get_text(strip=True)
        
    except Exception as e:
        logger.warning(f"    Amazon検索エラー: {e}")
    return info


def fetch_cosme_url(product_name: str, brand: str = None) -> dict:
    """@cosme検索結果からURLだけ取得（軽量版）"""
    info = {}
    try:
        query = f"{brand} {product_name}" if brand else product_name
        url = f"https://www.cosme.net/search/products?word={requests.utils.quote(query)}"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return info
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        link = soup.select_one('a[href*="/product/"]') or soup.select_one('a[href*="/products/"]')
        if link:
            href = link.get('href', '')
            if not href.startswith('http'):
                href = 'https://www.cosme.net' + href
            info['cosme_url'] = href
        
    except Exception as e:
        logger.warning(f"    @cosme検索エラー: {e}")
    return info


def generate_product_details(product_name: str, brand: str = None, category: str = None) -> dict:
    """Gemini AIを使って商品の詳細情報を生成する"""
    info = {}
    
    prompt = f"""あなたはコスメの専門家です。以下のコスメ商品について、正確な情報を提供してください。

商品名: {product_name}
ブランド: {brand or '不明'}
カテゴリ: {category or '不明'}

以下のJSON形式で回答してください。知らない情報や確信がない情報は null を入れてください。
嘘や推測の情報は絶対に入れないでください。

{{
  "description": "商品の簡潔な説明文（100〜200文字程度）",
  "features": ["特徴1", "特徴2", "特徴3"],
  "ingredients": "主な成分（わかる場合のみ。全成分表示ではなく主要成分を記載）",
  "volume": "容量（例: 30ml, 12g など）",
  "how_to_use": "基本的な使い方（50〜100文字程度）",
  "price": "定価（税込）※わかる場合のみ"
}}

重要:
- 嘘の情報は絶対に入れないこと
- 確信がない場合は null にすること
- 日本語で回答すること
- JSON以外の文字を含めないこと"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # JSON部分を抽出
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            text = text.split('```')[1].split('```')[0].strip()
        
        data = json.loads(text)
        
        if data.get('description'):
            info['description'] = data['description']
        if data.get('features') and isinstance(data['features'], list):
            info['features'] = json.dumps(data['features'], ensure_ascii=False)
        if data.get('ingredients'):
            info['ingredients'] = data['ingredients']
        if data.get('volume'):
            info['volume'] = data['volume']
        if data.get('how_to_use'):
            info['how_to_use'] = data['how_to_use']
        if data.get('price'):
            info['price'] = data['price']
        
    except json.JSONDecodeError as e:
        logger.warning(f"    JSON解析エラー: {e}")
    except Exception as e:
        logger.warning(f"    Gemini生成エラー: {e}")
    
    return info


def enrich_product(product: Product, db) -> int:
    """1商品の情報を充実させる"""
    updated = 0
    
    # 1. Gemini AIで商品詳細を生成
    logger.info(f"  Gemini AI で商品情報を生成中...")
    ai_info = generate_product_details(product.name, product.brand, product.category)
    
    # 2. Amazon URLと価格を取得（軽量検索のみ）
    if not product.amazon_url:
        logger.info(f"  Amazon URL を取得中...")
        amazon_info = fetch_amazon_url_and_price(product.name, product.brand)
        ai_info.update({k: v for k, v in amazon_info.items() if v})
        time.sleep(1)
    
    # 3. @cosme URLを取得
    if not product.cosme_url:
        logger.info(f"  @cosme URL を取得中...")
        cosme_info = fetch_cosme_url(product.name, product.brand)
        ai_info.update({k: v for k, v in cosme_info.items() if v})
        time.sleep(1)
    
    # 情報を更新（既存の値は上書きしない）
    for field, value in ai_info.items():
        if value and (not getattr(product, field, None)):
            setattr(product, field, value)
            display_val = str(value)[:80]
            logger.info(f"    ✓ {field}: {display_val}{'...' if len(str(value)) > 80 else ''}")
            updated += 1
    
    if updated:
        db.commit()
    
    return updated


def main():
    db = SessionLocal()
    products = db.query(Product).all()
    
    logger.info(f"対象商品: {len(products)}件\n")
    
    total_updated = 0
    for i, product in enumerate(products, 1):
        logger.info(f"[{i}/{len(products)}] {product.name} ({product.brand})")
        
        # 既に情報が充実している場合はスキップ
        if product.description and product.features and product.amazon_url:
            logger.info(f"  → スキップ（詳細情報は既に充実）")
            continue
        
        fields_updated = enrich_product(product, db)
        total_updated += fields_updated
        
        if fields_updated == 0:
            logger.info(f"  → 新しい情報なし")
        else:
            logger.info(f"  → {fields_updated}項目更新")
        
        time.sleep(2)  # Gemini APIレート制限対策
    
    db.close()
    logger.info(f"\n=== 完了: {total_updated}フィールドを更新 ===")


if __name__ == "__main__":
    main()
