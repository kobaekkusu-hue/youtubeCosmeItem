from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

class YouTubeService:
    def __init__(self):
        if not YOUTUBE_API_KEY:
            logger.warning("YOUTUBE_API_KEY not found in environment variables.")
        self.youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

    def resolve_channel_id(self, channel_input: str) -> str:
        """
        チャンネルURL/ハンドル/IDからチャンネルIDを解決する。
        対応形式:
          - https://www.youtube.com/@handle
          - https://www.youtube.com/channel/UCxxxxxxx
          - https://www.youtube.com/c/ChannelName
          - UCxxxxxxx（直接ID）
        """
        import re
        from urllib.parse import urlparse

        # 既にチャンネルID形式の場合
        if channel_input.startswith('UC') and len(channel_input) == 24:
            return channel_input

        parsed = urlparse(channel_input)
        path = parsed.path.strip('/')

        # @handle 形式
        handle_match = re.match(r'@(.+)', path)
        if handle_match:
            handle = handle_match.group(0)  # @付き
            try:
                # forHandle で検索
                request = self.youtube.channels().list(
                    part="id",
                    forHandle=handle_match.group(1)
                )
                response = request.execute()
                items = response.get('items', [])
                if items:
                    return items[0]['id']
            except Exception as e:
                logger.warning(f"ハンドル解決エラー ({handle}): {e}")
                # フォールバック: search API で検索
                try:
                    request = self.youtube.search().list(
                        part="snippet",
                        q=handle,
                        type="channel",
                        maxResults=1
                    )
                    response = request.execute()
                    items = response.get('items', [])
                    if items:
                        return items[0]['snippet']['channelId']
                except Exception as e2:
                    logger.error(f"チャンネル検索エラー: {e2}")
            return None

        # /channel/UCxxxxxxx 形式
        channel_match = re.match(r'channel/(UC[\w-]+)', path)
        if channel_match:
            return channel_match.group(1)

        # /c/ChannelName 形式
        c_match = re.match(r'c/(.+)', path)
        if c_match:
            try:
                request = self.youtube.search().list(
                    part="snippet",
                    q=c_match.group(1),
                    type="channel",
                    maxResults=1
                )
                response = request.execute()
                items = response.get('items', [])
                if items:
                    return items[0]['snippet']['channelId']
            except Exception as e:
                logger.error(f"チャンネル名解決エラー: {e}")

        logger.error(f"チャンネルIDを解決できません: {channel_input}")
        return None

    def get_channel_videos(self, channel_id: str, max_results: int = 50) -> list:
        """
        チャンネルの動画一覧を取得する。
        uploads プレイリスト経由で最新動画を取得。
        
        Returns:
            list: 各動画の snippet 情報（title, description, videoId等）
        """
        try:
            # チャンネルの uploads プレイリストIDを取得
            ch_request = self.youtube.channels().list(
                part="contentDetails",
                id=channel_id
            )
            ch_response = ch_request.execute()
            items = ch_response.get('items', [])
            if not items:
                logger.error(f"チャンネルが見つかりません: {channel_id}")
                return []
            
            uploads_playlist_id = items[0]['contentDetails']['relatedPlaylists']['uploads']
            
            # プレイリストから動画を取得
            videos = []
            next_page_token = None
            
            while len(videos) < max_results:
                pl_request = self.youtube.playlistItems().list(
                    part="snippet",
                    playlistId=uploads_playlist_id,
                    maxResults=min(50, max_results - len(videos)),
                    pageToken=next_page_token
                )
                pl_response = pl_request.execute()
                
                for item in pl_response.get('items', []):
                    video_id = item['snippet']['resourceId']['videoId']
                    videos.append({
                        'video_id': video_id,
                        'title': item['snippet']['title'],
                        'description': item['snippet'].get('description', ''),
                        'channel_name': item['snippet']['channelTitle'],
                        'published_at': item['snippet']['publishedAt'],
                        'thumbnail_url': item['snippet']['thumbnails'].get('high', {}).get('url', ''),
                    })
                
                next_page_token = pl_response.get('nextPageToken')
                if not next_page_token:
                    break
            
            logger.info(f"チャンネル {channel_id} から {len(videos)} 本の動画を取得")
            return videos
            
        except Exception as e:
            logger.error(f"チャンネル動画取得エラー: {e}")
            return []


    def search_videos(self, query: str, max_results: int = 10):
        """
        Search for videos on YouTube.
        """
        try:
            request = self.youtube.search().list(
                part="snippet",
                q=query,
                type="video",
                maxResults=max_results,
                relevanceLanguage="ja",
                regionCode="JP"
            )
            response = request.execute()
            return response.get('items', [])
        except Exception as e:
            logger.error(f"Error searching videos: {e}")
            return []

    def get_video_details(self, video_id: str):
        """
        Get detailed information for a specific video.
        """
        try:
            request = self.youtube.videos().list(
                part="snippet,contentDetails,statistics",
                id=video_id
            )
            response = request.execute()
            items = response.get('items', [])
            if items:
                return items[0]
            return None
        except Exception as e:
            logger.error(f"Error getting video details: {e}")
            return None

    def get_transcript(self, video_id: str):
        """
        Get the transcript for a video using youtube-transcript-api.
        Returns a list of dicts with 'text', 'start', 'duration'.
        """
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            # Filter for Japanese or auto-generated Japanese
            try:
                transcript = transcript_list.find_transcript(['ja'])
            except NoTranscriptFound:
                transcript = transcript_list.find_generated_transcript(['ja'])
            
            return transcript.fetch()
        except Exception as e:
            logger.warning(f"Standard transcript fetch failed for {video_id}: {e}. Trying manual fallback.")
            return self._get_transcript_manual(video_id)

    def _get_transcript_manual(self, video_id: str):
        """
        Fallback method to get transcript using yt-dlp.
        """
        try:
            from yt_dlp import YoutubeDL
            import requests
            import re
            
            logger.info(f"Attempting yt-dlp fetch for {video_id}...")
            
            ydl_opts = {
                'skip_download': True,
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['ja'],
                'quiet': True,
            }
            
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                
                # Check for subtitles
                subs = info.get('requested_subtitles')
                if not subs:
                    logger.warning(f"No subtitles found via yt-dlp for {video_id}")
                    return None
                
                ja_sub = subs.get('ja')
                if not ja_sub:
                    logger.warning(f"No 'ja' subtitles found via yt-dlp for {video_id}")
                    return None
                    
                url = ja_sub.get('url')
                if not url:
                    return None
                    
                # Fetch content (it's usually VTT or SRV/XML)
                res = requests.get(url)
                if res.status_code != 200:
                    logger.error(f"Failed to fetch subtitle content from {url}")
                    return None
                
                content = res.text
                
                # Simple VTT parser to extract text and timestamps
                # VTT format:
                # 00:00:00.120 --> 00:00:01.589
                # Text
                
                transcript_data = []
                
                # Regex for VTT timestamp line: 00:00:00.000 --> 00:00:00.000
                time_pattern = re.compile(r'(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})')
                
                lines = content.splitlines()
                current_start = 0.0
                current_duration = 0.0
                
                for i, line in enumerate(lines):
                    match = time_pattern.search(line)
                    if match:
                        start_str = match.group(1)
                        end_str = match.group(2)
                        
                        def parse_time(t_str):
                            h, m, s = t_str.split(':')
                            return float(h) * 3600 + float(m) * 60 + float(s)
                            
                        current_start = parse_time(start_str)
                        current_duration = parse_time(end_str) - current_start
                        
                        # Get text from next lines until empty line or next timestamp
                        text_parts = []
                        j = i + 1
                        while j < len(lines):
                            next_line = lines[j].strip()
                            if not next_line:
                                break
                            if time_pattern.search(next_line):
                                break
                            # Remove VTT tags like <c>...</c>, <00:00:00.000>
                            clean_line = re.sub(r'<[^>]+>', '', next_line)
                            if clean_line:
                                text_parts.append(clean_line)
                            j += 1
                        
                        if text_parts:
                            transcript_data.append({
                                'text': " ".join(text_parts),
                                'start': current_start,
                                'duration': current_duration
                            })
                            
                return transcript_data

        except Exception as e:
            logger.error(f"yt-dlp fetch failed for {video_id}: {e}")
            return None
