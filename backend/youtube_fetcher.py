import requests
import re
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import random # For supplemental topic selection and comment count

class YouTubeShortsSlangFetcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"
        # Define supplemental topics internally for the hybrid search logic
        self.supplemental_search_topics = ["gaming", "food review", "funny moments", "dance", "pets", "memes", "reactions"]
        # REMOVED: self.slang_terms initialization


    def search_shorts(self, query: str, max_results: int = 10, page_token: Optional[str] = None) -> (List[Dict], Optional[str]):
        """Search YouTube Shorts videos related to a topic, supporting pagination."""
        url = f"{self.base_url}/search"
        params = {
            'key': self.api_key,
            'q': query + " #shorts", # Append #shorts for better filtering
            'part': 'snippet',
            'type': 'video',
            'maxResults': max_results,
            'order': 'viewCount', # Prioritize popular videos
            'relevanceLanguage': 'en', # Prefer English results
            'videoDuration': 'short', # Explicitly request short videos (<4 mins, YT API limitation)
        }
        if page_token:
            params['pageToken'] = page_token

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            items = data.get('items', [])
            video_ids = [item['id']['videoId'] for item in items if item.get('id', {}).get('videoId')]
            next_page_token = data.get('nextPageToken')
            # Pass video_ids directly to get_video_details
            return self.get_video_details(video_ids), next_page_token
        except requests.exceptions.Timeout:
             print(f"   ⚠️ Timeout searching Shorts for '{query}'. Skipping page.")
             return [], None
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error searching Shorts for '{query}': {e}")
            return [], None
        except Exception as e:
             print(f"   ❌ Unexpected error during search for '{query}': {e}")
             return [], None


    def get_video_details(self, video_ids: List[str]) -> List[Dict]:
        """Get detailed video information - FILTER for embeddable videos WITH comments and likely English."""
        if not video_ids:
            return []
        url = f"{self.base_url}/videos"
        # Request snippet, contentDetails, statistics, AND status parts
        params = {
            'key': self.api_key,
            'id': ','.join(video_ids),
            'part': 'snippet,contentDetails,statistics,status' # Added 'status'
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            items = response.json().get('items', [])
            videos = []

            for item in items:
                snippet = item.get('snippet', {})
                stats = item.get('statistics', {})
                content_details = item.get('contentDetails', {})
                status = item.get('status', {}) # GET status object

                # --- FILTERS ---
                # 1. Skip videos that are not embeddable
                if not status.get('embeddable', False):
                    continue

                # 2. Skip videos with disabled comments or very few comments
                comment_count_str = stats.get('commentCount')
                if comment_count_str is None:
                    continue
                try:
                    comment_count = int(comment_count_str)
                    if comment_count < 10: # Require at least 10 comments
                        continue
                except ValueError:
                    continue

                # 3. Filter for actual Shorts (<= 60 seconds)
                duration_str = content_details.get('duration')
                if not duration_str:
                    continue
                duration_seconds = self.parse_duration(duration_str)
                if duration_seconds <= 0 or duration_seconds > 60:
                    continue

                # 4. Filter for likely English videos
                default_lang = snippet.get('defaultLanguage', '').lower()
                default_audio_lang = snippet.get('defaultAudioLanguage', '').lower()
                if default_lang and not default_lang.startswith('en'):
                    continue
                if default_audio_lang and not default_audio_lang.startswith('en'):
                    continue
                # --- END FILTERS ---


                thumbnails = snippet.get('thumbnails', {})
                thumbnail_url = (thumbnails.get('maxres') or thumbnails.get('high') or
                                 thumbnails.get('medium') or thumbnails.get('default', {})).get('url', '')

                videos.append({
                    'video_id': item['id'],
                    'title': snippet.get('title', 'No Title'),
                    'description': snippet.get('description', ''),
                    'channel': snippet.get('channelTitle', 'Unknown Channel'),
                    'channel_id': snippet.get('channelId', ''),
                    'thumbnail': thumbnail_url,
                    'duration_seconds': duration_seconds,
                    'view_count': int(stats.get('viewCount', 0)),
                    'like_count': int(stats.get('likeCount', 0)),
                    'comment_count': comment_count,
                    'url': f"https://www.youtube.com/shorts/{item['id']}"
                })

            return videos
        except requests.exceptions.Timeout:
             print("   ⚠️ Timeout getting video details. Skipping batch.")
             return []
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error getting video details: {e}")
            return []
        except Exception as e:
             print(f"   ❌ Unexpected error getting video details: {e}")
             return []

    def get_video_comments(self, video_id: str) -> List[Dict]: # Removed max_results default
        """Fetch the top 5-10 comments for a single video - filtering for English."""
        num_comments_to_fetch = random.randint(10, 20) # <-- FETCH RANDOM NUMBER OF COMMENTS
        url = f"{self.base_url}/commentThreads"
        params = {
            'key': self.api_key,
            'videoId': video_id,
            'part': 'snippet',
            'maxResults': num_comments_to_fetch, # Use the random number
            'order': 'topRated', # Sort by popularity
            'textFormat': 'plainText'
        }

        try:
            response = requests.get(url, params=params, timeout=8)

            if 400 <= response.status_code < 500:
                return []

            response.raise_for_status()
            items = response.json().get('items', [])

            comments = []
            for item in items:
                top_level_comment = item.get('snippet', {}).get('topLevelComment', {})
                if not top_level_comment: continue
                comment_id = top_level_comment.get('id')
                snippet = top_level_comment.get('snippet')
                if not snippet or not comment_id: continue

                text = snippet.get('textDisplay')
                if not text: continue

                # Filter primarily English comments
                if self.is_english_text(text):
                    comments.append({
                        'comment_id': comment_id,
                        'text': text,
                        'author': snippet.get('authorDisplayName', 'Unknown Author'),
                        'author_channel_url': snippet.get('authorChannelUrl', ''),
                        'like_count': snippet.get('likeCount', 0),
                        'published_at': snippet.get('publishedAt', ''),
                        'reply_count': item.get('snippet', {}).get('totalReplyCount', 0)
                    })

            return comments

        except requests.exceptions.Timeout:
             return []
        except requests.exceptions.RequestException as e:
             return []
        except Exception as e:
             return []

    def fetch_comments_parallel(self, video_ids: List[str]) -> Dict[str, List[Dict]]: # Removed max_results default
        """Fetch comments for multiple videos in parallel (fetches 5-10 per video)."""
        results = {}
        max_workers = min(10, len(video_ids) if video_ids else 1)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # The random number is determined inside get_video_comments now
            future_to_video = {
                executor.submit(self.get_video_comments, vid): vid
                for vid in video_ids
            }

            for future in as_completed(future_to_video):
                video_id = future_to_video[future]
                try:
                    comments = future.result()
                    if comments: # Store if comments were found
                        results[video_id] = comments
                except Exception as e:
                    print(f"   ⚠️ Error processing comments future for {video_id}: {e}")
                    results[video_id] = [] # Ensure key exists even on error

        return results

    def fetch_shorts(self, topics: List[str], shorts_per_topic: int = 15) -> List[Dict]: # Removed comments_per_short default here
        """
        Main function: Fetch shorts, get their top 5-10 comments.
        Implements Hybrid Fetching and returns ALL suitable videos.
        """
        final_shorts_data = []
        processed_video_ids = set()

        print(f"\n🔍 Searching {len(topics)} topics for top comments...")
        start_time = time.time()

        # --- Hybrid Fetching Logic (remains the same concept) ---
        is_custom_search = len(topics) == 1 and topics[0].lower() not in self.supplemental_search_topics # case-insensitive check
        search_plan = []

        if is_custom_search:
            custom_topic = topics[0]
            print(f"   🎯 Custom search detected for: '{custom_topic}'. Adding supplemental topics...")
            search_plan.append({"topic": custom_topic, "count": shorts_per_topic})
            num_supplemental = 3
            # Ensure supplemental topics list doesn't include the custom topic (case-insensitive)
            available_supplemental = [t for t in self.supplemental_search_topics if t.lower() != custom_topic.lower()]
            if available_supplemental:
                 num_supplemental = min(num_supplemental, len(available_supplemental))
                 supplemental_to_add = random.sample(available_supplemental, num_supplemental)
                 for supp_topic in supplemental_to_add:
                      # Fetch fewer supplemental videos
                      search_plan.append({"topic": supp_topic, "count": max(3, shorts_per_topic // (num_supplemental + 1))})
                 print(f"   Supplemental topics added: {supplemental_to_add}")
            else:
                 print("   No supplemental topics available to add.")
        else:
            # Standard search: fetch requested count for each topic
            for topic in topics:
                search_plan.append({"topic": topic, "count": shorts_per_topic})
        # --- End Hybrid Logic ---


        total_videos_found = 0

        for plan_item in search_plan:
            topic = plan_item["topic"]
            target_count = plan_item["count"]
            print(f"\n   Fetching topic: '{topic}' (target: {target_count} shorts)...")

            topic_videos = []
            next_page_token = None
            # Adjust max_pages based on target_count, aiming for roughly target_count results
            # Each page fetches up to 50 results (API limit)
            max_pages_needed = max(1, (target_count + 49) // 50) # Calculate pages needed
            max_pages = min(max_pages_needed, 3) # Limit to max 3 pages to control API usage

            for page in range(max_pages):
                print(f"      Fetching page {page + 1}/{max_pages}...")
                # Adjust maxResults per page call
                results_per_page = min(target_count - len(topic_videos), 50)
                if results_per_page <= 0: break # Stop if we already have enough

                shorts_page, next_page_token = self.search_shorts(
                    topic,
                    max_results=results_per_page,
                    page_token=next_page_token
                )

                if shorts_page:
                    new_shorts_on_page = [s for s in shorts_page if s['video_id'] not in processed_video_ids]
                    if new_shorts_on_page:
                         topic_videos.extend(new_shorts_on_page)
                         processed_video_ids.update(s['video_id'] for s in new_shorts_on_page)
                         # Stop fetching pages if we hit the target count for this topic
                         if len(topic_videos) >= target_count:
                             print(f"      Reached target count ({target_count}) for '{topic}'.")
                             break
                    # else: # Less verbose logging
                         # print("      All shorts on this page were duplicates or filtered.")

                # Stop if no more pages
                if not next_page_token:
                    break

            print(f"      Found {len(topic_videos)} total new, suitable shorts for '{topic}'.")

            if not topic_videos:
                continue

            video_ids_to_fetch = [s['video_id'] for s in topic_videos]

            # Fetch comments in parallel (will fetch 5-10 per video internally)
            print(f"      Fetching top 5-10 comments for {len(video_ids_to_fetch)} new videos...")
            comments_dict = self.fetch_comments_parallel(video_ids_to_fetch)

            # Process each new short
            for short in topic_videos:
                video_id = short['video_id']
                # Get the fetched comments, default to empty list if none found
                top_comments = comments_dict.get(video_id, [])

                # Add top comments to the short dictionary
                short['top_comments'] = top_comments # NEW FIELD

                final_shorts_data.append(short) # Add ALL suitable videos
                total_videos_found += 1

            print(f"      ✅ Processed {len(topic_videos)} videos for this topic.")


        elapsed = time.time() - start_time
        print(f"\n⏱️ Total fetch time: {elapsed:.1f}s")
        print(f"📊 Found {total_videos_found} total suitable short videos\n") # Updated log message

        # Shuffle results before returning for variety
        random.shuffle(final_shorts_data)
        return final_shorts_data


    def parse_duration(self, duration_str: str) -> int:
        """Convert ISO 8601 duration to seconds. Handles missing components."""
        if not duration_str or not duration_str.startswith('P'):
            return 0
        pattern = r'P(?:(\d+)D)?T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration_str)
        seconds = 0
        if match:
             days = int(match.group(1) or 0)
             hours = int(match.group(2) or 0)
             minutes = int(match.group(3) or 0)
             secs = int(match.group(4) or 0)
             seconds = (days * 86400) + (hours * 3600) + (minutes * 60) + secs
        elif duration_str == 'P0D' or duration_str == 'PT0S':
             seconds = 0
        elif duration_str == 'PT':
             seconds = 0
        else:
             simple_pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
             simple_match = re.match(simple_pattern, duration_str)
             if simple_match:
                 hours = int(simple_match.group(1) or 0)
                 minutes = int(simple_match.group(2) or 0)
                 secs = int(simple_match.group(3) or 0)
                 seconds = (hours * 3600) + (minutes * 60) + secs
             else:
                  print(f"   ⚠️ Could not parse duration: {duration_str}")

        return seconds

    def is_english_text(self, text: str) -> bool:
        """Simple heuristic to check if text is primarily English (or uses Latin script)."""
        if not text:
            return False
        text_length = len(text)
        if text_length == 0: return False

        try:
            latin_based_chars = sum(1 for c in text if (
                'a' <= c.lower() <= 'z' or
                '0' <= c <= '9' or
                c in ' .,!?"\'()[]{}<>:;-_+=*&^%$#@~`/\n\t'
            ))
            ratio = latin_based_chars / text_length
            return ratio > 0.8
        except Exception:
            return False

