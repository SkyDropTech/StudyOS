from youtube_transcript_api import YouTubeTranscriptApi
import urllib.parse as urlparse
from urllib.parse import parse_qs

def extract_video_id(url: str):
    """Safely extracts the video ID from any YouTube URL format."""
    url = url.strip()
    if "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0].split("/")[0]
    if "v=" in url:
        parsed = urlparse.urlparse(url)
        return parse_qs(parsed.query).get('v', [None])[0]
    if "youtube.com/shorts/" in url:
        return url.split("shorts/")[1].split("?")[0]
    if len(url) == 11 and " " not in url:
        return url
    return None

def get_youtube_transcript(url: str) -> str:
    try:
        video_id = extract_video_id(url)
        if not video_id:
            return "Error: Invalid YouTube URL format. Please use a standard youtube.com or youtu.be link."
        
        # youtube-transcript-api v1.x requires an instance
        api = YouTubeTranscriptApi()
        
        # Try English first, then fall back to any available language
        try:
            transcript = api.fetch(video_id, languages=['en'])
        except Exception:
            try:
                transcript = api.fetch(video_id, languages=['en-US', 'en-GB'])
            except Exception:
                # Get any available transcript
                transcript_list = api.list(video_id)
                first = next(iter(transcript_list))
                transcript = first.fetch()
        
        full_text = " ".join([snippet.text for snippet in transcript])
        return full_text
    except Exception as e:
        err = str(e)
        if "No transcripts" in err or "Could not retrieve" in err:
            return "Error: This video does not have captions/subtitles available. Please try a different video."
        return f"Error extracting transcript: {err}"
