import os
import sys
import subprocess
import argparse
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def run_command(command, cwd="."):
    """コマンドを実行し、エラーがあれば中断する"""
    logger.info(f"Running: {command}")
    env = os.environ.copy()
    # ローカルDBへの登録時は DATABASE_URL を空にする (SQLiteを使うため)
    if "register_yt_cosme.py" in command or "enrich_product_info.py" in command:
        env["DATABASE_URL"] = ""
    
    result = subprocess.run(command, shell=True, cwd=cwd, env=env)
    if result.returncode != 0:
        logger.error(f"Command failed with exit code {result.returncode}: {command}")
        sys.exit(result.returncode)

def main():
    parser = argparse.ArgumentParser(description="YouTubeから商品情報を収集、詳細化、Supabaseへ同期する")
    parser.add_argument("url", help="対象のYouTube動画URL")
    args = parser.parse_args()

    video_url = args.url

    # 1. collect_yt_cosme.py のVIDEO_URLを動的に書き換えて実行
    # ※ 本来は引数で渡せるようにすべきだが、既存スクリプトの構造を活かす
    # ここでは一時的に collect_yt_cosme.py を読み込み、URLを設定して実行する
    logger.info("=== STEP 1: 商品情報の抽出 ===")
    # collect_yt_cosme.py を一時的に修正するのではなく、環境変数や引数で渡せるようにリファクタリングするのが理想
    # 今回はシンプルに、VIDEO_URL を定数として持つスクリプトの特性を考慮し、
    # VIDEO_URL を引数として受け取れるようにリファクタリングするか、
    # あるいは collect_yt_cosme.py をそのまま利用する（現在は固定されている）
    
    # リファクタリング済みの collect_yt_cosme.py を想定（URLを引数で受け取れるようにする）
    run_command(f"python collect_yt_cosme.py --url {video_url}")

    # 2. register_yt_cosme.py の実行 (動画情報を動的に)
    logger.info("=== STEP 2: データベース登録 ===")
    run_command(f"python register_yt_cosme.py --url {video_url}")

    # 3. enrich_product_info.py の実行
    logger.info("=== STEP 3: 詳細情報の補完 (Gemini) ===")
    run_command("python enrich_product_info.py")

    # 4. migrate_local_to_supabase.py の実行
    logger.info("=== STEP 4: Supabase への同期 ===")
    run_command("python migrate_local_to_supabase.py")

    logger.info("=== 全ての工程が完了しました！ ===")

if __name__ == "__main__":
    main()
