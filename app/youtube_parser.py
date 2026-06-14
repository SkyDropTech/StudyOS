# app/youtube_parser.py
from youtube_transcript_api import YouTubeTranscriptApi
import urllib.parse as urlparse
from urllib.parse import parse_qs

def extract_video_id(url: str) -> str:
    """Extracts the YouTube Video ID from a standard URL or youtu.be link."""
    if "youtu.be" in url:
        return url.split("/")[-1].split("?")[0]
    
    parsed = urlparse.urlparse(url)
    return parse_qs(parsed.query).get('v', [None])[0]

def get_youtube_transcript(url: str) -> str:
    """Fetches the transcript and combines it into a single text block."""
    try:
        video_id = extract_video_id(url)
        if not video_id:
            return "Error: Invalid YouTube URL"
        
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        
        # Combine all the text pieces into one giant string
        full_text = " ".join([chunk['text'] for chunk in transcript_list])
        return full_text
        
    except Exception as e:
        return f"Error extracting transcript: {str(e)}"