import requests
import re
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

class YouTubeShortsSlangFetcher:
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
        """Search YouTube Shorts videos related to a topic."""
        url = f"{self.base_url}/search"
        params = {
            'key': self.api_key,
            'q': query,
            'part': 'snippet',
            'type': 'video',
            'maxResults': max_results,
            'order': 'viewCount',
            'relevanceLanguage': 'en',
            'regionCode': 'US'
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            items = response.json().get('items', [])
            video_ids = [item['id']['videoId'] for item in items]
            return self.get_video_details(video_ids)
        except Exception as e:
            print(f"❌ Error searching Shorts: {e}")
            return []

    def get_video_details(self, video_ids: List[str]) -> List[Dict]:
        """Get detailed video information - FILTER for videos WITH comments"""
        if not video_ids:
            return []
        url = f"{self.base_url}/videos"
        params = {
            'key': self.api_key,
            'id': ','.join(video_ids),
            'part': 'snippet,contentDetails,statistics'
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            items = response.json().get('items', [])
            videos = []
            
            for item in items:
                stats = item.get('statistics', {})
                
                # CRITICAL: Skip videos with disabled comments
                comment_count = int(stats.get('commentCount', 0))
                if comment_count == 0:
                    continue
                
                duration_str = item['contentDetails']['duration']
                duration_seconds = self.parse_duration(duration_str)
                
                # Filter for Shorts (under 60 seconds)
                if duration_seconds > 60:
                    continue

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
                    'view_count': int(stats.get('viewCount', 0)),
                    'like_count': int(stats.get('likeCount', 0)),
                    'comment_count': comment_count,
                    'url': f"https://www.youtube.com/shorts/{item['id']}"
                })
            
            return videos
        except Exception as e:
            print(f"❌ Error getting video details: {e}")
            return []

    def get_video_comments(self, video_id: str, max_results: int = 50) -> List[Dict]:
        """Fetch comments for a single video - with proper error handling"""
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
            response = requests.get(url, params=params, timeout=8)
            
            # Handle 403 (comments disabled) gracefully
            if response.status_code == 403:
                return []  # Silently skip
            
            response.raise_for_status()
            items = response.json().get('items', [])
            
            comments = []
            for item in items:
                snippet = item['snippet']['topLevelComment']['snippet']
                text = snippet['textDisplay']
                
                # Filter English comments
                if self.is_english_text(text):
                    comments.append({
                        'comment_id': item['id'],
                        'text': text,
                        'author': snippet['authorDisplayName'],
                        'author_channel_url': snippet.get('authorChannelUrl', ''),
                        'like_count': snippet['likeCount'],
                        'published_at': snippet['publishedAt'],
                        'reply_count': item['snippet']['totalReplyCount']
                    })
            
            return comments
            
        except Exception:
            return []  # Silently fail for individual videos

    def fetch_comments_parallel(self, video_ids: List[str], max_results: int = 50) -> Dict[str, List[Dict]]:
        """Fetch comments for multiple videos in parallel - FAST"""
        results = {}
        
        # Use ThreadPoolExecutor for parallel requests
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all tasks
            future_to_video = {
                executor.submit(self.get_video_comments, vid, max_results): vid 
                for vid in video_ids
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_video):
                video_id = future_to_video[future]
                try:
                    comments = future.result()
                    results[video_id] = comments
                except Exception as e:
                    print(f"⚠️ Error for {video_id}: {e}")
                    results[video_id] = []
        
        return results

    def fetch_shorts(self, topics: List[str], shorts_per_topic: int = 10, 
                     comments_per_short: int = 50, custom_slang: List[str] = None) -> List[Dict]:
        """
        Main function: Fetch shorts with slang comments
        OPTIMIZED for speed and reliability
        """
        all_shorts_data = []
        slang_terms = set(self.slang_terms)
        
        if custom_slang:
            slang_terms.update(s.lower() for s in custom_slang)
        
        print(f"\n🔍 Searching {len(topics)} topics for shorts...")
        start_time = time.time()
        
        for topic_idx, topic in enumerate(topics, 1):
            print(f"\n[{topic_idx}/{len(topics)}] Topic: '{topic}'")
            
            # Search for videos
            shorts = self.search_shorts(topic, max_results=shorts_per_topic)
            print(f"   Found {len(shorts)} shorts with comments enabled")
            
            if not shorts:
                continue
            
            # Get all video IDs
            video_ids = [s['video_id'] for s in shorts]
            
            # Fetch comments in parallel - FAST!
            print(f"   Fetching comments from {len(video_ids)} videos...")
            comments_dict = self.fetch_comments_parallel(video_ids, max_results=comments_per_short)
            
            # Process each short
            shorts_with_slang = 0
            for short in shorts:
                video_id = short['video_id']
                comments = comments_dict.get(video_id, [])
                
                if not comments:
                    continue
                
                # Find comments with slang
                comments_with_slang = []
                for comment in comments:
                    detected_slang = self.detect_slang_in_text(comment['text'], slang_terms)
                    if detected_slang:
                        comment['detected_slang'] = detected_slang
                        comments_with_slang.append(comment)
                
                if comments_with_slang:
                    short['comments_with_slang'] = comments_with_slang
                    short['slang_comment_count'] = len(comments_with_slang)
                    short['unique_slang_terms'] = list(set(
                        slang for c in comments_with_slang for slang in c['detected_slang']
                    ))
                    all_shorts_data.append(short)
                    shorts_with_slang += 1
            
            print(f"   ✅ {shorts_with_slang} shorts have slang comments")
        
        elapsed = time.time() - start_time
        print(f"\n⏱️ Total time: {elapsed:.1f}s")
        print(f"📊 Found {len(all_shorts_data)} shorts with slang\n")
        
        return all_shorts_data

    def detect_slang_in_text(self, text: str, slang_terms: set) -> List[str]:
        """Detect slang terms with word boundaries (accurate matching)"""
        text_lower = text.lower()
        found = []
        
        for slang in slang_terms:
            pattern = r'\b' + re.escape(slang) + r'\b'
            if re.search(pattern, text_lower):
                found.append(slang)
        
        return found

    def parse_duration(self, duration_str: str) -> int:
        """Convert ISO 8601 duration to seconds"""
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration_str)
        if match:
            h, m, s = [int(g or 0) for g in match.groups()]
            return h * 3600 + m * 60 + s
        return 0

    def is_english_text(self, text: str) -> bool:
        """Check if text is primarily English"""
        if not text:
            return False
        ascii_chars = sum(1 for c in text if ord(c) < 128)
        return ascii_chars / len(text) > 0.8