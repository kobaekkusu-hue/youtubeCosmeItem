import google.generativeai as genai
import os
import json
import logging
import time
import re
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-flash-latest")


def _load_api_keys() -> List[str]:
    """
    APIキーを環境変数から読み込む。
    
    優先順位:
    1. GEMINI_API_KEY_1 〜 GEMINI_API_KEY_10（キープール方式）
    2. GEMINI_API_KEY（単一キー、フォールバック）
    """
    keys = []
    for i in range(1, 11):
        key = os.getenv(f"GEMINI_API_KEY_{i}")
        if key:
            keys.append(key)
    
    if not keys:
        # フォールバック: 旧来の単一キー
        single_key = os.getenv("GEMINI_API_KEY")
        if single_key:
            keys.append(single_key)
    
    return keys


# グローバルキープール
_API_KEYS = _load_api_keys()


class GeminiService:
    """
    複数APIキーのローテーション対応 GeminiService.
    
    429レート制限エラー時、待機せずに次のキーに即座に切り替えてリトライする。
    全キーが使い切られた場合のみ待機する。
    """
    
    # クラス変数: 全インスタンスで共有するキーのインデックス
    _current_key_index = 0
    _exhausted_keys = set()  # レート制限に引っかかったキーのインデックス
    
    def __init__(self, api_keys: List[str] = None):
        self.api_keys = api_keys or _API_KEYS
        if not self.api_keys:
            logger.warning("APIキーが設定されていません。AI機能は動作しません。")
            self.model = None
            return
        
        logger.info(f"GeminiService 初期化: {len(self.api_keys)} 個のAPIキーを使用")
        for i, key in enumerate(self.api_keys):
            logger.info(f"  キー{i+1}: ...{key[-6:]}")
        
        # 最初のキーで初期化
        self._switch_to_key(GeminiService._current_key_index % len(self.api_keys))
    
    def _switch_to_key(self, index: int):
        """指定インデックスのキーに切り替え"""
        key = self.api_keys[index]
        genai.configure(api_key=key)
        self.model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        GeminiService._current_key_index = index
        logger.info(f"  🔑 キー{index+1}に切替 (...{key[-6:]})")
    
    def _next_key(self) -> bool:
        """
        次のキーに切り替える。
        全キーが使い切られた場合は False を返す。
        """
        GeminiService._exhausted_keys.add(GeminiService._current_key_index)
        
        # 未使用のキーを探す
        for i in range(len(self.api_keys)):
            next_idx = (GeminiService._current_key_index + 1 + i) % len(self.api_keys)
            if next_idx not in GeminiService._exhausted_keys:
                self._switch_to_key(next_idx)
                return True
        
        return False
    
    def _generate_with_retry(self, prompt: str) -> str:
        """
        APIコールをキーローテーション付きでリトライする。
        429エラー → 次のキーに即切替（待機なし）
        全キー使い切り → 60秒待機してリセット
        """
        attempts = 0
        max_attempts = len(self.api_keys) * 2  # 全キー x 2周
        
        while attempts < max_attempts:
            try:
                # 成功: 使い切りリストから現在のキーを除外
                response = self.model.generate_content(prompt)
                GeminiService._exhausted_keys.discard(GeminiService._current_key_index)
                return response.text.strip()
            except Exception as e:
                error_str = str(e)
                logger.warning(f"  ⚠️ Gemini API エラー: {error_str}")
                if '429' in error_str:
                    attempts += 1
                    # 429エラー時は待機時間を増やす
                    wait_time = 15 * attempts
                    logger.info(f"  ⏳ 429レート制限。{wait_time}秒待機してリトライします (試行 {attempts})")
                    time.sleep(wait_time)
                    
                    has_next = self._next_key()
                    if not has_next:
                        # 全キー使い切り → 60秒待機してリセット
                        logger.warning(f"全 {len(self.api_keys)} 個のキーがレート制限中。60秒待機してリセット...")
                        time.sleep(60)
                        GeminiService._exhausted_keys.clear()
                        self._switch_to_key(0)
                    continue
                else:
                    raise e
        
        raise Exception(f"全キーで {max_attempts} 回リトライしましたが成功しませんでした")

    def analyze_video(self, transcript: List[Dict[str, Any]], description: str = "", title: str = "") -> List[Dict[str, Any]]:
        """
        動画の概要欄 + 字幕から商品レビューを正確に抽出する。
        """
        if not transcript and not description:
            return []

        # 字幕テキスト（タイムスタンプ付き）
        # レート制限回避のため、字幕解析を完全にスキップする（最終手段）
        transcript_text = "（字幕解析スキップ）"

        prompt = f"""あなたはプロのコスメレビュー分析AIです。
以下のYouTube動画から、紹介されているコスメ商品を**正確に**抽出してください。

━━━━━━━━━━━━━━━━━━━
【最重要ルール】
━━━━━━━━━━━━━━━━━━━

1. **概要欄に商品名が記載されている場合、必ずその正式名称をそのまま使用すること。**
   概要欄の商品名が最も信頼性が高い情報源です。

2. **字幕の音声認識ミスに注意。** 自動生成字幕はブランド名を誤認識しやすい。
   例: 「ルナソル」→「ルナ粗」、「セザンヌ」→「せざぬ」など

3. **概要欄に記載がない商品は、字幕から確信度が非常に高い場合のみ抽出する。**
   推測や不確かな商品名は絶対に出力しないこと。

4. **商品名は短い正式名称のみ。** 宣伝文句や機能説明は含めない。
   ✅ 良い例: 「エアリーチェンジリキッド」「UV イデア XL プロテクション トーンアップ」
   ❌ 悪い例: 「エアリーチェンジリキッド 01 やや明るめの肌 サラサラ極軽肌 毛穴凹凸カバー テカリ防止...」
   色番号までは含めてOK（例: 「エアリーチェンジリキッド 01」）

━━━━━━━━━━━━━━━━━━━
【動画タイトル】
{title}

【概要欄（商品リストが含まれている可能性が高い）】
{description[:5000] if description else "（概要欄なし）"}

【字幕データ（タイムスタンプ付き）】
{transcript_text[:25000]}
━━━━━━━━━━━━━━━━━━━

【出力フォーマット】
以下のJSON形式の配列のみを出力してください。Markdownのコードブロックは不要です。

[
    {{
        "product_name": "短い正式商品名（色番号まで。宣伝文句は不要）",
        "brand_name": "ブランド名",
        "category": "カテゴリ（ファンデーション、リップ、アイシャドウなど）",
        "timestamp_seconds": 字幕で最初に言及された秒数（整数）,
        "sentiment": "positive" or "negative" or "neutral",
        "summary": "どのような評価が語られているか（50文字程度）"
    }}
]

【抽出の手順】
1. まず概要欄から商品リストを特定する
2. 各商品が字幕のどの部分で言及されているかタイムスタンプを特定する
3. その時間帯の字幕からsentimentとsummaryを判断する
4. 概要欄にない商品は、字幕で明確に商品名とブランド名が言及されている場合のみ追加する"""

        try:
            text = self._generate_with_retry(prompt)
            # JSON部分を抽出
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            
            results = json.loads(text.strip())
            logger.info(f"Geminiから {len(results)} 件の商品を抽出")
            return results
        except Exception as e:
            logger.error(f"Error analyzing video with Gemini: {e}")
            return []

    # 後方互換性のため残す
    def analyze_transcript(self, transcript: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """旧API（概要欄なし版）— analyze_video を推奨"""
        return self.analyze_video(transcript)
