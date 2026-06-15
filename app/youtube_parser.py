from youtube_transcript_api import YouTubeTranscriptApi
import urllib.parse as urlparse
from urllib.parse import parse_qs

def extract_video_id(url: str):
    """Safely extracts the video ID from any YouTube URL format."""
    if "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    if "v=" in url:
        parsed = urlparse.urlparse(url)
        return parse_qs(parsed.query).get('v', [None])[0]
    if len(url) == 11:
        return url
    return None

def get_youtube_transcript(url: str) -> str:
    try:
        video_id = extract_video_id(url)
        if not video_id:
            return "Error: Invalid YouTube URL format."
        
        # Pull the transcript
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        
        # Join into a single string
        full_text = " ".join([chunk['text'] for chunk in transcript_list])
        return full_text
    except Exception as e:
        return f"Error extracting transcript: {str(e)}"