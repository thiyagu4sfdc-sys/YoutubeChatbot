"""YouTube transcript extraction and processing utilities."""
import re
from typing import List, Dict, Optional
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound


def extract_video_id(url: str) -> Optional[str]:
    """
    Extract YouTube video ID from various URL formats.
    
    Args:
        url: YouTube URL in various formats
        
    Returns:
        Video ID if found, None otherwise
    """
    patterns = [
        r"youtube\.com/watch\?v=(.{11})",
        r"youtu\.be/(.{11})",
        r"youtube\.com/embed/(.{11})",
        r"youtu\.be/(.{11})"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # Check if URL itself is just a video ID
    if re.match(r"^[a-zA-Z0-9_-]{11}$", url):
        return url
    
    return None


def get_transcript(video_id: str, languages: List[str] = None) -> Optional[List[Dict]]:
    """
    Fetch transcript for a YouTube video.
    
    Args:
        video_id: YouTube video ID
        languages: Preferred languages (e.g., ['en', 'es'])
        
    Returns:
        List of transcript entries with 'text' and 'start' keys
        
    Raises:
        Various exceptions if transcript unavailable
    """
    if not languages:
        languages = ['en']
    
    try:
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id)
        return transcript
    except TranscriptsDisabled:
        raise ValueError(f"Transcripts are disabled for video {video_id}")
    except NoTranscriptFound:
        raise ValueError(f"No transcript found for video {video_id} in languages {languages}")
    except Exception as e:
        raise Exception(f"Error fetching transcript: {str(e)}")


def clean_transcript_text(text: str) -> str:
    """
    Clean transcript text by removing junk characters.
    
    Args:
        text: Raw transcript text
        
    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special YouTube markers
    text = re.sub(r'\[.*?\]', '', text)
    return text.strip()


def transcript_to_text(transcript: List[Dict]) -> str:
    """
    Convert transcript list to continuous text.
    
    Args:
        transcript: List of transcript entries
        
    Returns:
        Continuous text
    """
    if not transcript:
        return ""
    
    text_parts = []
    for entry in transcript:
        if hasattr(entry, 'get'):
            text_parts.append(entry.get('text', ''))
        else:
            text_parts.append(getattr(entry, 'text', ''))
    full_text = ' '.join(text_parts)
    return clean_transcript_text(full_text)


def format_timestamp(seconds: float) -> str:
    """
    Format seconds to HH:MM:SS format.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted timestamp string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
