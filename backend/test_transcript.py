from youtube_transcript_api import YouTubeTranscriptApi
import inspect

print("YouTubeTranscriptApi attributes:")
print(dir(YouTubeTranscriptApi))

try:
    video_id = "epHygxXbZt0" # TED Talk: What makes a good life?
    print(f"\nAttempting to fetch transcript for {video_id}:")
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    
    print("Available transcripts:")
    for t in transcript_list:
        print(f"- {t.language} ({t.language_code}) - {t.is_generated} - {t.is_translatable}")
        
    transcript = transcript_list.find_transcript(['en'])
    print(f"\nFetching 'en' transcript...")
    print(transcript.fetch()[:2])
except Exception as e:
    print(f"Error: {e}")
