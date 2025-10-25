import requests
import json
from typing import List, Dict
import re

class YouTubeShortsSlangFetcher:
    """
    Fetches YouTube Shorts videos and comments containing slang terms
    English language only
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"
        
        # Popular slang terms to search for
        self.slang_terms = {
            'fr', 'ngl', 'tbh', 'smh', 'imo', 'lol', 'lmao', 
            'bruh', 'bet', 'bussin', 'sheesh', 'sigma', 'lit', 
            'lowkey', 'highkey', 'cap', 'nocap', 'vibe', 'vibes',
            'slay', 'goat', 'savage', 'flex', 'sus', 'mid',
            'w', 'l', 'ratio', 'fam', 'stan', 'simp', 'based',
            'yeet', 'slaps', 'valid', 'mood', 'hits different'
        }
    
    def search_shorts(self, query: str, max_results: int = 20) -> List[Dict]:
        """
        Search for YouTube Shorts videos (ENGLISH ONLY)
        """
        url = f"{self.base_url}/search"
        params = {
            'key': self.api_key,
            'q': query,
            'part': 'snippet',
            'type': 'video',
            'videoDuration': 'short',
            'maxResults': max_results,
            'order': 'viewCount',
            'relevanceLanguage': 'en',  # English only
            'regionCode': 'US'  # US region (helps with English content)
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            items = response.json().get('items', [])
            
            # Get additional video details
            video_ids = [item['id']['videoId'] for item in items]
            detailed_videos = self.get_video_details(video_ids)
            
            # Filter for actual Shorts (under 60 seconds) and English
            shorts = []
            for video in detailed_videos:
                duration = video.get('duration_seconds', 0)
                # Check if video language is English
                if duration <= 60 and self.is_english_content(video):
                    shorts.append(video)
            
            return shorts
            
        except requests.exceptions.RequestException as e:
            print(f"Error searching Shorts: {e}")
            return []
    
    def is_english_content(self, video: Dict) -> bool:
        """Check if video content is primarily English"""
        # Check for English indicators in title and description
        text = (video.get('title', '') + ' ' + video.get('description', '')).lower()
        
        # Simple heuristic: if it contains mostly ASCII and common English patterns
        ascii_ratio = sum(c.isascii() for c in text) / max(len(text), 1)
        
        # If more than 80% ASCII characters, likely English
        return ascii_ratio > 0.8
    
    def get_video_details(self, video_ids: List[str]) -> List[Dict]:
        """Get detailed information about videos"""
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
                
                # Extract high quality thumbnail
                thumbnails = item['snippet']['thumbnails']
                thumbnail_url = (thumbnails.get('maxres') or 
                               thumbnails.get('high') or 
                               thumbnails.get('medium') or 
                               thumbnails.get('default', {})).get('url', '')
                
                videos.append({
                    'video_id': item['id'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'channel': item['snippet']['channelTitle'],
                    'channel_id': item['snippet']['channelId'],
                    'published_at': item['snippet']['publishedAt'],
                    'thumbnail': thumbnail_url,
                    'duration_seconds': duration_seconds,
                    'view_count': int(item['statistics'].get('viewCount', 0)),
                    'like_count': int(item['statistics'].get('likeCount', 0)),
                    'comment_count': int(item['statistics'].get('commentCount', 0)),
                    'url': f"https://www.youtube.com/shorts/{item['id']}",
                    'embed_url': f"https://www.youtube.com/embed/{item['id']}"
                })
            
            return videos
            
        except requests.exceptions.RequestException as e:
            print(f"Error getting video details: {e}")
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
    
    def is_english_text(self, text: str) -> bool:
        """Check if text is primarily English"""
        # Check ASCII ratio
        ascii_ratio = sum(c.isascii() for c in text) / max(len(text), 1)
        return ascii_ratio > 0.8
    
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
    
    def fetch_shorts_with_slang_comments(self, topics: List[str], 
                                         shorts_per_topic: int = 10,
                                         comments_per_short: int = 50) -> List[Dict]:
        """
        Main function: Fetch English Shorts with comments containing slang
        """
        all_shorts_data = []
        
        for topic in topics:
            print(f"\n🔍 Searching Shorts for: '{topic}'...")
            
            shorts = self.search_shorts(topic, max_results=shorts_per_topic)
            print(f"   Found {len(shorts)} English Shorts")
            
            for short in shorts:
                video_id = short['video_id']
                print(f"   📹 {short['title'][:50]}...")
                
                comments = self.get_video_comments(video_id, max_results=comments_per_short)
                
                # Filter comments with slang
                comments_with_slang = []
                for comment in comments:
                    detected_slang = self.detect_slang_in_text(comment['text'])
                    if detected_slang:
                        comment['detected_slang'] = detected_slang
                        comments_with_slang.append(comment)
                
                if comments_with_slang:
                    short['comments_with_slang'] = comments_with_slang
                    short['slang_comment_count'] = len(comments_with_slang)
                    short['unique_slang_terms'] = list(set(
                        slang for comment in comments_with_slang 
                        for slang in comment['detected_slang']
                    ))
                    all_shorts_data.append(short)
                    print(f"      ✅ {len(comments_with_slang)} slang comments")
        
        return all_shorts_data
    
    def save_to_json(self, data: List[Dict], filename: str = 'shorts_data.json'):
        """Save data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Saved {len(data)} shorts to {filename}")


# ==================== MAIN SCRIPT ====================

def get_user_topics():
    """Get topics from user"""
    print("\n🎯 Enter topics to search (English content only)")
    print("   Examples: gaming, food review, music, dance, comedy")
    print("   Type 'done' when finished\n")
    
    topics = []
    while True:
        topic = input(f"Topic #{len(topics) + 1}: ").strip()
        if topic.lower() == 'done':
            break
        if topic:
            topics.append(topic)
            print(f"   ✓ Added: {topic}")
    
    return topics

def get_custom_slang():
    """Allow custom slang terms"""
    print("\n📝 Add custom slang terms? (y/n): ", end='')
    if input().lower() == 'y':
        print("   Enter terms separated by commas:")
        custom = input("   > ").strip()
        if custom:
            return set(term.strip().lower() for term in custom.split(','))
    return set()

if __name__ == "__main__":
    print("=" * 70)
    print("🎬 YOUTUBE SHORTS SLANG FETCHER (ENGLISH ONLY)")
    print("=" * 70)
    
    # API Key
    print("\n🔑 YouTube API Key")
    API_KEY = input("Enter your API key: ").strip()
    9
    if not API_KEY:
        print("❌ API key required!")
        exit()
    
    # Initialize
    fetcher = YouTubeShortsSlangFetcher(API_KEY)
    
    # Custom slang
    custom_slang = get_custom_slang()
    if custom_slang:
        fetcher.slang_terms.update(custom_slang)
        print(f"   ✓ Added {len(custom_slang)} custom terms")
    
    # Topics
    topics = get_user_topics()
    if not topics:
        print("\n⚠️ No topics. Using defaults:")
        topics = ["gaming", "food review", "funny moments"]
        for t in topics:
            print(f"   - {t}")
    
    # Configuration
    print("\n⚙️ Configuration:")
    shorts_per_topic = int(input("Shorts per topic (5-25, default 10): ").strip() or "10")
    comments_per_short = int(input("Comments per short (20-100, default 50): ").strip() or "50")
    
    print(f"\n📊 Searching {len(topics)} topics...")
    print(f"   Detecting {len(fetcher.slang_terms)} slang terms")
    print(f"   Language: English only\n")
    
    # Fetch
    shorts_data = fetcher.fetch_shorts_with_slang_comments(
        topics=topics,
        shorts_per_topic=shorts_per_topic,
        comments_per_short=comments_per_short
    )
    
    # Summary
    print(f"\n" + "=" * 70)
    print(f"📊 RESULTS")
    print(f"=" * 70)
    
    if not shorts_data:
        print("⚠️ No results found. Try:")
        print("   - Different topics")
        print("   - More shorts per topic")
        exit()
    
    print(f"✅ Found {len(shorts_data)} shorts with slang")
    total_comments = sum(s['slang_comment_count'] for s in shorts_data)
    print(f"💬 Total slang comments: {total_comments}")
    
    all_slang = set()
    for s in shorts_data:
        all_slang.update(s['unique_slang_terms'])
    print(f"🏷️  Unique slang: {', '.join(sorted(all_slang))}")
    
    # Top 3
    print(f"\n🔥 TOP 3 SHORTS:\n")
    for i, short in enumerate(sorted(shorts_data, 
                                     key=lambda x: x['slang_comment_count'], 
                                     reverse=True)[:3], 1):
        print(f"{i}. {short['title'][:60]}")
        print(f"   📊 {short['view_count']:,} views | {short['slang_comment_count']} slang comments")
        print(f"   🔗 {short['url']}")
        print(f"   🏷️  {', '.join(short['unique_slang_terms'])}")
        print()
    
    # Save
    filename = input("💾 Save as (default: shorts_data.json): ").strip() or "shorts_data.json"
    fetcher.save_to_json(shorts_data, filename)
    
    print("\n✅ Done! Use the JSON file in your frontend app.")
    print(f"   File: {filename}")
    print(f"   Shorts: {len(shorts_data)}")