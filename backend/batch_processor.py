import typer
from typing import List, Optional
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import Product, Video, Review
from services.youtube import YouTubeService
from services.gemini import GeminiService
import logging
import re
import unicodedata
from difflib import SequenceMatcher
import json
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import time

# Build DB tables if they don't exist
Base.metadata.create_all(bind=engine)

app = typer.Typer()
logger = logging.getLogger(__name__)

# Amazon検索用ヘッダー
_SEARCH_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
}

def resolve_official_product_info(product_name: str, brand_name: str = None) -> dict:
    """
    Amazon の検索結果から画像URL・価格を取得する。
    商品名はGemini が概要欄から抽出した正式名称をそのまま使用する。
    
    Returns:
        dict: {'name': 商品名, 'image_url': 画像URL, 'price': 価格文字列}
    """
    result = {'name': product_name, 'image_url': '', 'price': None}
    
    # Amazon から画像・価格を取得
    try:
        query = f"{brand_name} {product_name}" if brand_name else product_name
        amazon_url = f"https://www.amazon.co.jp/s?k={requests.utils.quote(query)}"
        resp = requests.get(amazon_url, headers=_SEARCH_HEADERS, timeout=10)
        
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            first_result = soup.select_one('[data-component-type="s-search-result"]')
            
            if first_result:
                # 画像URL（Amazonは商品名は使わず画像だけ取得）
                img_el = first_result.select_one('img.s-image')
                if img_el:
                    src = img_el.get('src', '')
                    if src.startswith('http'):
                        result['image_url'] = src
                
                # 価格
                price_el = first_result.select_one('.a-price .a-offscreen')
                if price_el:
                    result['price'] = price_el.get_text(strip=True)
                    logger.info(f"  価格: {result['price']}")
        
        time.sleep(1)
        
    except Exception as e:
        logger.warning(f"Amazon検索エラー ({product_name}): {e}")
    
    return result

def normalize_name(name: str) -> str:
    """商品名を正規化する（スペース除去、全角半角統一、カッコ内除去）"""
    if not name:
        return ""
    # NFKC正規化（全角→半角、濁点統一など）
    name = unicodedata.normalize('NFKC', name)
    # 括弧とその中身を除去（例: (Medicube) → 空）
    name = re.sub(r'[\(（][^)）]*[\)）]', '', name)
    # 空白を全て除去
    name = re.sub(r'\s+', '', name)
    # 小文字化（英字の表記揺れ対応）
    name = name.lower()
    return name.strip()

def find_matching_product(db: Session, product_name: str, brand_name: str = None) -> Optional[Product]:
    """既存の商品から名寄せで一致するものを探す"""
    normalized_new = normalize_name(product_name)
    if not normalized_new:
        return None
    
    # 全商品を取得して比較（データ量が少ないうちはこれで十分）
    all_products = db.query(Product).all()
    
    best_match = None
    best_score = 0.0
    
    for existing in all_products:
        normalized_existing = normalize_name(existing.name)
        
        # 完全一致（正規化後）
        if normalized_new == normalized_existing:
            return existing
        
        # 類似度計算
        score = SequenceMatcher(None, normalized_new, normalized_existing).ratio()
        
        # ブランド名も考慮（ブランドが一致すれば閾値を下げる）
        if brand_name and existing.brand:
            brand_score = SequenceMatcher(
                None, 
                normalize_name(brand_name), 
                normalize_name(existing.brand)
            ).ratio()
            if brand_score > 0.7:
                score += 0.1  # ブランド一致ボーナス
        
        if score > best_score:
            best_score = score
            best_match = existing
    
    # 閾値0.85以上なら同一商品と判定
    if best_score >= 0.85 and best_match:
        logger.info(f"名寄せ: '{product_name}' → 既存 '{best_match.name}' (スコア: {best_score:.2f})")
        return best_match
    
    return None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.command()
def run_batch(query: str = "コスメ レビュー", max_videos: int = 5):
    """
    Search for videos, analyze them, and save results to the database.
    """
    db = SessionLocal()
    youtube_service = YouTubeService()
    gemini_service = GeminiService()

    logger.info(f"Starting batch process for query: {query}")

    # 1. Search Videos
    videos = youtube_service.search_videos(query, max_results=max_videos)
    logger.info(f"Found {len(videos)} videos.")

    for item in videos:
        video_id = item['id']['videoId']
        snippet = item['snippet']
        process_video_item(db, youtube_service, gemini_service, video_id, snippet)

    db.close()
    logger.info("Batch process completed.")

@app.command()
def process_urls(
    urls: List[str],
    api_key: str = typer.Option(None, help="Gemini APIキー (オーバーライド用)"),
    main_only: bool = typer.Option(False, help="商品抽出(メイン処理)のみ実行し、エンリッチ処理をスキップする")
):
    """
    Process specific YouTube videos by URL.
    Example: python batch_processor.py process-urls https://www.youtube.com/watch?v=... --api-key AIza... --main-only
    """
    from urllib.parse import urlparse, parse_qs

    db = SessionLocal()
    youtube_service = YouTubeService()
    
    # APIキーが指定された場合はそれを使用、なければ環境変数からロード
    keys = [api_key] if api_key else None
    gemini_service = GeminiService(api_keys=keys)

    for url in urls:
        # Extract Video ID
        parsed = urlparse(url)
        if parsed.hostname in ('youtu.be', 'www.youtu.be'):
            video_id = parsed.path[1:]
        elif parsed.hostname in ('youtube.com', 'www.youtube.com'):
            video_id = parse_qs(parsed.query).get('v', [None])[0]
        else:
            logger.warning(f"Invalid YouTube URL: {url}")
            continue

        if not video_id:
            logger.warning(f"Could not extract video ID from: {url}")
            continue

        logger.info(f"Processing URL: {url} -> ID: {video_id}")
        
        # Fetch Video Details
        video_details = youtube_service.get_video_details(video_id)
        if not video_details:
            logger.error(f"Could not fetch details for video {video_id}")
            continue
        
        snippet = video_details['snippet']
        process_video_item(
            db, 
            youtube_service, 
            gemini_service, 
            video_id, 
            snippet, 
            skip_enrich=main_only
        )

    db.close()
    logger.info("Custom video process completed.")

def process_video_item(db: Session, youtube_service: YouTubeService, gemini_service: GeminiService, video_id: str, snippet: dict, enrich_gemini_service: GeminiService = None, skip_enrich: bool = False):
    title = snippet['title']
    channel_name = snippet['channelTitle']
    description = snippet.get('description', '')  # 概要欄テキストを取得
    published_at_str = snippet['publishedAt']
    # Handle different date formats or ensure consistency. API usually returns ISO 8601
    try:
        published_at = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
    except ValueError:
        # Fallback if format is different
        published_at = datetime.utcnow()

    thumbnail_url = snippet['thumbnails']['high']['url']

    # Check if video already exists
    existing_video = db.query(Video).filter(Video.id == video_id).first()
    if existing_video:
        logger.info(f"Video {video_id} already exists. Skipping.")
        return

    logger.info(f"Processing video: {title} ({video_id})")
    if description:
        logger.info(f"概要欄あり: {len(description)}文字")

    # 2. Get Transcript
    transcript = youtube_service.get_transcript(video_id)
    if not transcript:
        if description:
            # 字幕なしでも概要欄があれば分析を続行
            logger.warning(f"字幕取得失敗 ({video_id})。概要欄のみで商品抽出を試みます。")
            transcript = [{"start": 0, "text": "（字幕なし）"}]
        else:
            logger.warning(f"No transcript and no description for video {video_id}. Skipping.")
            return

    # 3. Analyze with Gemini（概要欄 + 字幕を渡す）
    logger.info(f"Analyzing video {video_id} with description + transcript...")
    try:
        analysis_results = gemini_service.analyze_video(
            transcript=transcript,
            description=description,
            title=title
        )
    except Exception as e:
        logger.error(f"Gemini analysis failed: {e}")
        return

    if not analysis_results:
        logger.info("No products found in video.")
        return

    # 4. Save to DB
    # Save Video
    new_video = Video(
        id=video_id,
        title=title,
        channel_name=channel_name,
        published_at=published_at,
        thumbnail_url=thumbnail_url
    )
    db.add(new_video)
    db.commit() # Commit video first to satisfy FK

    for result in analysis_results:
        product_name = result.get('product_name')
        if not product_name:
            continue

        # 名寄せ: 正規化名と類似度で既存商品を検索
        brand_name = result.get('brand_name')
        product = find_matching_product(db, product_name, brand_name)
        if not product:
            # 新規商品: Amazon から正規の商品名・画像・価格を取得
            logger.info(f"新規商品検出: '{product_name}' → 公式情報を検索中...")
            official_info = resolve_official_product_info(product_name, brand_name)
            
            product = Product(
                name=official_info['name'],
                brand=brand_name,
                category=result.get('category'),
                image_url=official_info['image_url'],
                price=official_info['price'],
            )
            db.add(product)
            db.commit()
            db.refresh(product)
            logger.info(f"新規商品登録: '{official_info['name']}' (ID: {product.id[:8]}...)")
            
            # 新規商品の詳細情報をGemini AIで生成
            if not skip_enrich:
                enrich_svc = enrich_gemini_service or gemini_service
                enrich_new_product(product, enrich_svc, db)
                time.sleep(1)  # API レート制限対策
            else:
                logger.info(f"  メイン処理のみ実行のためエンリッチ処理をスキップします")
        # Save Review
        review = Review(
            product_id=product.id,
            video_id=video_id,
            timestamp_seconds=result.get('timestamp_seconds', 0),
            sentiment=result.get('sentiment', 'neutral'),
            summary=result.get('summary', '')
        )
        db.add(review)
    
    db.commit()
    count = db.query(Video).count()
    logger.info(f"Saved results for video {video_id}. Total videos in DB: {count}")


def enrich_new_product(product: Product, gemini_service: GeminiService, db):
    """新規登録した商品の詳細情報をGemini AIで生成する"""
    try:
        prompt = f"""以下のコスメ商品について、正確な情報を提供してください。

商品名: {product.name}
ブランド: {product.brand or '不明'}
カテゴリ: {product.category or '不明'}

以下のJSON形式で回答。確信がない情報は null にしてください。嘘は絶対に入れないこと。

{{
  "description": "商品の簡潔な説明文（100〜200文字程度）",
  "features": ["特徴1", "特徴2", "特徴3"],
  "ingredients": "主な成分（わかる場合のみ）",
  "volume": "容量（例: 30ml, 12g）",
  "how_to_use": "基本的な使い方（50〜100文字程度）"
}}

JSON以外の文字を含めないこと。"""

        response = gemini_service.model.generate_content(prompt)
        text = response.text.strip()
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            text = text.split('```')[1].split('```')[0].strip()
        
        data = json.loads(text)
        
        if data.get('description'):
            product.description = data['description']
        if data.get('features') and isinstance(data['features'], list):
            product.features = json.dumps(data['features'], ensure_ascii=False)
        if data.get('ingredients'):
            product.ingredients = data['ingredients']
        if data.get('volume'):
            product.volume = data['volume']
        if data.get('how_to_use'):
            product.how_to_use = data['how_to_use']
        
        db.commit()
        logger.info(f"  商品詳細を生成しました")
    except Exception as e:
        logger.warning(f"  商品詳細の生成に失敗: {e}")


# ============================================================
# 3段階フィルタリングパイプライン
# ============================================================

# ① タイトルフィルター: 「ベストコスメ」「ベスコス」を含む動画のみ通す
TITLE_PASS_KEYWORDS = [
    'ベストコスメ',
    'ベスコス',
]

def filter_by_title(title: str, description: str = '') -> bool:
    """
    ①タイトル判定: 「ベストコスメ」「ベスコス」を含む動画のみ通す。
    
    Returns:
        True = 通過（処理対象）、False = スキップ
    """
    text = (title + ' ' + description).lower()
    # パスワードのいずれかがタイトルまたは概要欄に含まれれば通す
    for keyword in TITLE_PASS_KEYWORDS:
        if keyword.lower() in text:
            return True
    return False


# ② 字幕密度判定用コスメ用語辞書
COSME_TERMS = [
    '発色', 'テクスチャ', '保湿', '乾燥', 'イエベ', 'ブルベ',
    '毛穴', 'カバー力', '崩れ', '色味', 'パケ', '円',
    '塗る', '仕上がり', 'ツヤ', 'マット', '下地', 'ラメ',
    'パウダー', 'リキッド', 'ファンデ', 'リップ', 'アイシャドウ',
    'チーク', 'マスカラ', 'アイライナー', 'コンシーラー',
    'プライマー', 'ハイライト', 'シェーディング', 'ベース',
    'スキンケア', '化粧水', '乳液', '美容液', 'クレンジング',
    '日焼け止め', 'SPF', 'UV', 'くすみ', 'トーンアップ',
    'フィット', 'ヨレ', 'テカリ', 'サラサラ', 'しっとり',
    'ナチュラル', '透明感', '血色', 'ツヤ肌', 'マット肌',
    'プチプラ', 'デパコス', 'コスメ', 'メイク',
]

def filter_by_transcript_density(transcript: list) -> float:
    """
    ②字幕密度判定: コスメ関連用語の出現率を計算する。
    
    Returns:
        float: コスメ用語密度（0.0〜1.0）。高いほどコスメ関連。
    """
    if not transcript:
        return 0.0
    
    # 字幕テキストを結合
    full_text = ' '.join([item.get('text', '') for item in transcript])
    total_chars = len(full_text)
    
    if total_chars == 0:
        return 0.0
    
    # コスメ用語の出現回数をカウント
    hit_count = 0
    for term in COSME_TERMS:
        hit_count += full_text.count(term)
    
    # 密度 = ヒット数 / 総文字数 * 100（パーセント）
    density = (hit_count / total_chars) * 100
    return density


# 字幕密度の閾値（%）: これ以上ならコスメ関連と判定
COSME_DENSITY_THRESHOLD = 0.3


def filter_by_ai_classification(
    gemini_service: GeminiService,
    title: str,
    description: str,
    transcript_sample: str
) -> bool:
    """
    ③AI分類: Gemini Flash で「コスメレビュー/紹介か？」を Yes/No 判定。
    
    Returns:
        True = コスメレビューと判定、False = コスメレビューではない
    """
    prompt = f"""以下のYouTube動画は「コスメ（化粧品）のレビューまたは紹介動画」ですか？
Yes か No のいずれか1単語のみで回答してください。

【タイトル】
{title}

【概要欄（冒頭）】
{description[:1000] if description else '（なし）'}

【字幕（冒頭）】
{transcript_sample[:1500]}
"""
    try:
        response = gemini_service.model.generate_content(prompt)
        answer = response.text.strip().lower()
        is_cosme = answer.startswith('yes') or 'yes' in answer
        return is_cosme
    except Exception as e:
        logger.warning(f"AI分類エラー: {e}")
        # エラー時は安全側（通す）
        return True


@app.command()
def process_channel(
    channel: str = typer.Argument(..., help="チャンネルURL、@ハンドル、またはチャンネルID"),
    max_videos: int = typer.Option(50, help="取得する最大動画数"),
    density_threshold: float = typer.Option(COSME_DENSITY_THRESHOLD, help="字幕密度閾値（%）"),
    skip_ai: bool = typer.Option(False, help="③AI分類をスキップする"),
    title_only: bool = typer.Option(False, help="①タイトル判定のみで②③をスキップ"),
):
    """
    特定YouTuberのチャンネルから動画をフィルタリングで収集する。
    
    ① タイトルに「ベストコスメ」「ベスコス」を含む動画のみ通過
    ② 字幕のコスメ用語密度が閾値以上の動画のみ通過（--title-only で省略可）
    ③ Gemini AI で「コスメレビューか？」を Yes/No 判定（--title-only で省略可）
    
    Example:
        python batch_processor.py process-channel https://www.youtube.com/@cosmemory --title-only
        python batch_processor.py process-channel https://www.youtube.com/@cosmemory --max-videos 20
    """
    db = SessionLocal()
    youtube_service = YouTubeService()

    # キープール方式の共有GeminiService（10個のキーを自動ローテーション）
    gemini_service = GeminiService()

    # チャンネルID解決
    logger.info(f"チャンネルを解決中: {channel}")
    channel_id = youtube_service.resolve_channel_id(channel)
    if not channel_id:
        logger.error(f"チャンネルIDを解決できません: {channel}")
        db.close()
        return
    logger.info(f"チャンネルID: {channel_id}")

    # チャンネルの動画一覧を取得
    videos = youtube_service.get_channel_videos(channel_id, max_results=max_videos)
    if not videos:
        logger.error("動画が見つかりませんでした")
        db.close()
        return

    logger.info(f"=== {len(videos)} 本の動画を取得。3段階フィルタリング開始 ===")

    stats = {'total': len(videos), 'pass_title': 0, 'pass_density': 0, 'pass_ai': 0, 'processed': 0, 'skipped_existing': 0}

    for i, video_info in enumerate(videos, 1):
        video_id = video_info['video_id']
        title = video_info['title']
        description = video_info['description']

        logger.info(f"\n[{i}/{len(videos)}] 📹 {title}")

        # 処理済みチェック
        existing = db.query(Video).filter(Video.id == video_id).first()
        if existing:
            logger.info(f"  ⏭️  既に処理済み。スキップ。")
            stats['skipped_existing'] += 1
            continue

        # ===== ① タイトル判定 =====
        if not filter_by_title(title, description):
            logger.info(f"  ❌ ①タイトル判定: 「ベストコスメ/ベスコス」が含まれていません → スキップ")
            continue
        logger.info(f"  ✅ ①タイトル判定: 通過")
        stats['pass_title'] += 1

        # ===== ② 字幕密度判定 =====
        if not title_only:
            transcript = youtube_service.get_transcript(video_id)
            if not transcript:
                # 字幕取得失敗時：タイトル判定を通過しているのでスキップせず先に進む
                logger.info(f"  ⚠️  ②字幕取得失敗 → タイトル判定通過済みのため、字幕密度チェックをスキップ")
                stats['pass_density'] += 1
            else:
                density = filter_by_transcript_density(transcript)
                if density < density_threshold:
                    logger.info(f"  ❌ ②字幕密度: {density:.2f}% < 閾値{density_threshold}% → スキップ")
                    continue
                logger.info(f"  ✅ ②字幕密度: {density:.2f}% ≥ 閾値{density_threshold}% → 通過")
                stats['pass_density'] += 1

            # ===== ③ AI分類 =====
            if not skip_ai:
                transcript_sample = ''
                if transcript:
                    transcript_sample = ' '.join([item.get('text', '') for item in transcript[:50]])
                is_cosme = filter_by_ai_classification(gemini_service, title, description, transcript_sample)
                if not is_cosme:
                    logger.info(f"  ❌ ③AI分類: コスメレビューではないと判定 → スキップ")
                    continue
                logger.info(f"  ✅ ③AI分類: コスメレビューと判定 → 通過")
                time.sleep(1)  # API レート制限対策
            stats['pass_ai'] += 1
        else:
            logger.info(f"  ⏩ ②③スキップ（--title-only モード）")
            stats['pass_density'] += 1
            stats['pass_ai'] += 1

        # ===== 詳細抽出 =====
        logger.info(f"  🔍 詳細抽出開始...")
        snippet = {
            'title': title,
            'channelTitle': video_info['channel_name'],
            'description': description,
            'publishedAt': video_info['published_at'],
            'thumbnails': {'high': {'url': video_info['thumbnail_url']}},
        }
        process_video_item(db, youtube_service, gemini_service, video_id, snippet)
        stats['processed'] += 1

    # 統計レポート
    logger.info(f"\n{'='*50}")
    logger.info(f"📊 処理結果サマリー")
    logger.info(f"{'='*50}")
    logger.info(f"  全動画数:        {stats['total']}")
    logger.info(f"  処理済スキップ:  {stats['skipped_existing']}")
    logger.info(f"  ①タイトル通過:   {stats['pass_title']}")
    logger.info(f"  ②字幕密度通過:   {stats['pass_density']}")
    logger.info(f"  ③AI分類通過:     {stats['pass_ai']}")
    logger.info(f"  詳細抽出完了:    {stats['processed']}")
    logger.info(f"{'='*50}")

    db.close()
    logger.info("チャンネル処理完了。")


if __name__ == "__main__":
    app()
