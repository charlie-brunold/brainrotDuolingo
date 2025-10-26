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

    def search_shorts(self, topic: str, max_results: int = 10):
        """
        Searches YouTube for Shorts matching the topic.
        Ensures only embeddable videos are returned.
        """
        results = []
        print(f"🎯 Searching YouTube Shorts for topic: {topic}")

        try:
            search_response = self.youtube.search().list(
                q=topic,
                part="snippet",
                type="video",
                videoDuration="short",
                maxResults=max_results * 2,  # fetch extras to filter out bad ones
                videoEmbeddable="true"
            ).execute()

            for item in search_response.get("items", []):
                video_id = item["id"]["videoId"]

                # Check if embeddable
                video_details = self.youtube.videos().list(
                    part="status,snippet,statistics",
                    id=video_id
                ).execute()

                if not video_details.get("items"):
                    continue

                video_info = video_details["items"][0]
                status = video_info.get("status", {})
                if not status.get("embeddable", False):
                    print(f"🚫 Skipping unembeddable video: {video_id}")
                    continue

                snippet = video_info["snippet"]
                stats = video_info.get("statistics", {})

                results.append({
                    "video_id": video_id,
                    "title": snippet.get("title", ""),
                    "description": snippet.get("description", ""),
                    "channel_title": snippet.get("channelTitle", ""),
                    "like_count": int(stats.get("likeCount", 0)) if "likeCount" in stats else 0,
                    "topic": topic,
                    "embeddable": True
                })

                if len(results) >= max_results:
                    break

        except Exception as e:
            print(f"⚠️ Error searching for topic '{topic}': {str(e)}")

        print(f"✅ Found {len(results)} embeddable shorts for '{topic}'")
        return results


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
        Main function: Fetch shorts and detect slang in comments.
        Returns ALL videos that meet basic criteria (commentable, short duration).
        
        If a single topic is provided (custom search), it also executes a broader search
        to interweave more content from the default list.
        """
        all_shorts_data = []
        slang_terms = set(self.slang_terms)
        
        if custom_slang:
            slang_terms.update(s.lower() for s in custom_slang)

        # Determine the effective list of topics to search
        search_topics = topics.copy()
        
        # Define SUPPLEMENTAL topics (previously "default")
        supplemental_topics = ["gaming", "food review", "funny moments", "dance", "pets"]
        
        # Determine if this is a focused custom search vs. a broad search
        is_focused_custom_search = len(topics) == 1 and topics[0] not in supplemental_topics
        
        if is_focused_custom_search:
             print(f"\n💡 Focused topic '{topics[0]}' detected. Interweaving with supplementary topics for variety.")
             # Add supplemental topics but search them minimally
             for supplemental_topic in supplemental_topics:
                 if supplemental_topic not in search_topics:
                     search_topics.append(supplemental_topic)
        
        print(f"\n🔍 Searching {len(search_topics)} topics for shorts...")
        start_time = time.time()
        
        total_shorts_with_slang = 0
        
        # Adjust results per topic based on how many searches we are doing
        if is_focused_custom_search:
             # Search the custom topic fully (at shorts_per_topic count)
             custom_topic_max = shorts_per_topic
             # Search supplemental topics minimally (2 results each)
             supplemental_topic_max = 2 
             
        for topic_idx, topic in enumerate(search_topics, 1):
            
            # Set max_results based on whether it's the custom topic or an interweaved topic
            if is_focused_custom_search and topic == topics[0]:
                max_results = custom_topic_max
            elif is_focused_custom_search and topic != topics[0]:
                max_results = supplemental_topic_max
            else:
                # If it's a regular multi-topic search, use the standard count
                max_results = shorts_per_topic
                
            print(f"\n[{topic_idx}/{len(search_topics)}] Topic: '{topic}' (Max: {max_results})")
            
            # Search for videos
            shorts = self.search_shorts(topic, max_results=max_results)
            print(f"   Found {len(shorts)} shorts with comments enabled")
            
            if not shorts:
                continue
            
            # Get all video IDs
            video_ids = [s['video_id'] for s in shorts]
            
            # Fetch comments in parallel - FAST!
            print(f"   Fetching comments from {len(video_ids)} videos...")
            comments_dict = self.fetch_comments_parallel(video_ids, max_results=comments_per_short)
            
            shorts_with_slang_count = 0
            
            # Process each short
            for short in shorts:
                video_id = short['video_id']
                comments = comments_dict.get(video_id, [])
                
                # --- NEW LOGIC: DETECT SLANG BUT APPEND ALL VIDEOS ---
                comments_with_slang = []
                
                if comments:
                    for comment in comments:
                        detected_slang = self.detect_slang_in_text(comment['text'], slang_terms)
                        if detected_slang:
                            comment['detected_slang'] = detected_slang
                            comments_with_slang.append(comment)
                
                # 1. Always attach the comment data, even if empty
                short['comments_with_slang'] = comments_with_slang
                short['slang_comment_count'] = len(comments_with_slang)
                short['unique_slang_terms'] = list(set(
                    slang for c in comments_with_slang for slang in c['detected_slang']
                ))
                
                # 2. APPEND ALL videos that are eligible (not just those with slang)
                all_shorts_data.append(short)
                
                if comments_with_slang:
                    shorts_with_slang_count += 1
                # --- END NEW LOGIC ---

            total_shorts_with_slang += shorts_with_slang_count
            print(f"   ✅ {shorts_with_slang_count} shorts have slang comments")
        
        elapsed = time.time() - start_time
        print(f"\n⏱️ Total time: {elapsed:.1f}s")
        print(f"📊 Found {len(all_shorts_data)} total short videos (of which {total_shorts_with_slang} contain slang)\n")
        
        return all_shorts_data

    def detect_slang_in_text(self, text: str, slang_terms: set) -> List[str]:
        """Detect slang terms with word boundaries (accurate matching)"""
        text_lower = text.lower()
        found = []
        
        for slang in slang_terms:
            # Handle multi-word slang like 'hits different'
            if ' ' in slang:
                pattern = re.escape(slang)
            else:
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
        # Simple check: 80% of characters are within the standard ASCII range
        ascii_chars = sum(1 for c in text if ord(c) < 128)
        return ascii_chars / len(text) > 0.8
