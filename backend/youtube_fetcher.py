# youtube_fetcher.py

import requests
import re
from typing import List, Dict

class YouTubeShortsSlangFetcher:
    """
    Fetches YouTube Shorts videos and comments containing slang terms (English only)
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.slang_terms = {
            'fr', 'ngl', 'tbh', 'smh', 'imo', 'lol', 'lmao', 
            'bruh', 'bet', 'bussin', 'sheesh', 'sigma', 'lit', 
            'lowkey', 'highkey', 'cap', 'nocap', 'vibe', 'vibes',
            'slay', 'goat', 'savage', 'flex', 'sus', 'mid',
            'w', 'l', 'ratio', 'fam', 'stan', 'simp', 'based',
            'yeet', 'slaps', 'valid', 'mood', 'hits different'
        }

    def search_shorts(self, query: str, max_results: int = 10) -> List[Dict]:
        url = f"{self.base_url}/search"
        params = {
            'key': self.api_key,
            'q': query,
            'part': 'snippet',
            'type': 'video',
            'videoDuration': 'short',
            'maxResults': max_results,
            'order': 'viewCount',
            'relevanceLanguage': 'en',
            'regionCode': 'US'
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            items = response.json().get('items', [])
            video_ids = [item['id']['videoId'] for item in items]
            return self.get_video_details(video_ids)
        except Exception as e:
            print("Error searching Shorts:", e)
            return []

    def get_video_details(self, video_ids: List[str]) -> List[Dict]:
        if not video_ids:
            return []
        url = f"{self.base_url}/videos"
        params = {
            'key': self.api_key,
            'id': ','.join(video_ids),
            'part': 'snippet,contentDetails,statistics'
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            items = response.json().get('items', [])
            videos = []
            for item in items:
                duration_str = item['contentDetails']['duration']
                duration_seconds = self.parse_duration(duration_str)
                thumbnails = item['snippet']['thumbnails']
                thumbnail_url = (thumbnails.get('maxres') or thumbnails.get('high') or
                                 thumbnails.get('medium') or thumbnails.get('default', {})).get('url', '')
                videos.append({
                    'video_id': item['id'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'channel': item['snippet']['channelTitle'],
                    'thumbnail': thumbnail_url,
                    'duration_seconds': duration_seconds,
                    'view_count': int(item['statistics'].get('viewCount', 0)),
                    # ADDED these two fields for the frontend
                    'like_count': int(item['statistics'].get('likeCount', 0)),
                    'comment_count': int(item['statistics'].get('commentCount', 0)),
                    'url': f"https://www.youtube.com/shorts/{item['id']}"
                })
            return videos
        except Exception as e:
            print("Error getting video details:", e)
            return []

    def parse_duration(self, duration_str: str) -> int:
        """Convert ISO 8601 duration to seconds"""
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration_str)
        if match:
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)
            return hours * 3600 + minutes * 60 + seconds
        return 0

    # youtube_fetcher.py - Replace fetch_shorts with this:

    def fetch_shorts(self, topics: List[str], shorts_per_topic: int = 10) -> List[Dict]:
        """Fetch videos, then enrich with slang comments."""
        all_shorts_data = []
        
        for topic in topics:
            # Step 1: Search and get details
            shorts = self.search_shorts(topic, max_results=shorts_per_topic)
            
            for short in shorts:
                # Filter for actual Shorts (under 60 seconds)
                if short.get('duration_seconds', 0) > 60:
                    continue
                    
                video_id = short['video_id']
                
                # Step 2: Fetch and filter comments
                comments = self.get_video_comments(video_id, max_results=50) # Max 50 comments
                
                comments_with_slang = []
                for comment in comments:
                    detected_slang = self.detect_slang_in_text(comment['text'])
                    if detected_slang:
                        comment['detected_slang'] = detected_slang
                        comments_with_slang.append(comment)
                
                if comments_with_slang:
                    # Step 3: Add enriched data to the short
                    short['comments_with_slang'] = comments_with_slang
                    short['slang_comment_count'] = len(comments_with_slang)
                    short['unique_slang_terms'] = list(set(
                        slang for comment in comments_with_slang 
                        for slang in comment['detected_slang']
                    ))
                    all_shorts_data.append(short)
        
        return all_shorts_data
    
    def get_video_comments(self, video_id: str, max_results: int = 100) -> List[Dict]:
        """Fetch comments for a specific video (ENGLISH ONLY)"""
        url = f"{self.base_url}/commentThreads"
        params = {
            'key': self.api_key,
            'videoId': video_id,
            'part': 'snippet',
            'maxResults': max_results,
            'order': 'relevance',
            'textFormat': 'plainText'
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            items = response.json().get('items', [])
            
            comments = []
            for item in items:
                comment_data = item['snippet']['topLevelComment']['snippet']
                comment_text = comment_data['textDisplay']
                
                # Filter for English comments only
                if self.is_english_text(comment_text):
                    comments.append({
                        'comment_id': item['id'],
                        'text': comment_text,
                        'author': comment_data['authorDisplayName'],
                        'author_channel_url': comment_data.get('authorChannelUrl', ''),
                        'like_count': comment_data['likeCount'],
                        'published_at': comment_data['publishedAt'],
                        'reply_count': item['snippet']['totalReplyCount']
                    })
            
            return comments
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching comments for {video_id}: {e}")
            return []
    
    def detect_slang_in_text(self, text: str) -> List[str]:
        """
        Detect which slang terms appear in text with accurate word boundary matching
        """
        text_lower = text.lower()
        found_slang = []
        
        for slang in self.slang_terms:
            # Use word boundaries to match exact words only
            pattern = r'\b' + re.escape(slang) + r'\b'
            if re.search(pattern, text_lower):
                found_slang.append(slang)
        
        return found_slang
    def is_english_text(self, text: str) -> bool:
        """
        Simple heuristic to filter English comments:
        Returns True if most characters are ASCII letters.
        """
        return all(ord(c) < 128 for c in text)
