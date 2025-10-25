# database.py
import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class VideoDatabase:
    """
    SQLite database for caching YouTube API calls
    """
    
    def __init__(self, db_path: str = "videos_cache.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Videos table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                video_id TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                channel TEXT,
                channel_id TEXT,
                thumbnail TEXT,
                duration_seconds INTEGER,
                view_count INTEGER,
                like_count INTEGER,
                comment_count INTEGER,
                url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Comments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                comment_id TEXT PRIMARY KEY,
                video_id TEXT,
                text TEXT,
                author TEXT,
                author_channel_url TEXT,
                like_count INTEGER,
                published_at TEXT,
                reply_count INTEGER,
                detected_slang TEXT,  -- JSON array of slang terms
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES videos (video_id)
            )
        ''')
        
        # Cache metadata table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topics TEXT,  -- JSON array of topics
                custom_slang TEXT,  -- JSON array of custom slang
                shorts_per_topic INTEGER,
                comments_per_short INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_cached_videos(self, topics: List[str], custom_slang: List[str], 
                         shorts_per_topic: int, comments_per_short: int) -> Optional[List[Dict]]:
        """
        Check if we have cached data for these parameters
        Returns cached videos if found and not expired, None otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if we have recent cache for these parameters
        topics_json = json.dumps(topics)
        custom_slang_json = json.dumps(custom_slang)
        
        cursor.execute('''
            SELECT * FROM cache_metadata 
            WHERE topics = ? AND custom_slang = ? 
            AND shorts_per_topic = ? AND comments_per_short = ?
            AND expires_at > datetime('now')
            ORDER BY created_at DESC LIMIT 1
        ''', (topics_json, custom_slang_json, shorts_per_topic, comments_per_short))
        
        cache_entry = cursor.fetchone()
        if not cache_entry:
            conn.close()
            return None
        
        # Get videos for this cache entry
        cursor.execute('''
            SELECT v.*, 
                   GROUP_CONCAT(c.comment_id) as comment_ids,
                   GROUP_CONCAT(c.text) as comment_texts,
                   GROUP_CONCAT(c.author) as comment_authors,
                   GROUP_CONCAT(c.like_count) as comment_likes,
                   GROUP_CONCAT(c.detected_slang) as comment_slang
            FROM videos v
            LEFT JOIN comments c ON v.video_id = c.video_id
            GROUP BY v.video_id
            ORDER BY v.created_at DESC
            LIMIT ?
        ''', (shorts_per_topic * len(topics),))
        
        videos = cursor.fetchall()
        if not videos:
            conn.close()
            return None
        
        # Convert to the expected format
        result = []
        for video in videos:
            video_data = {
                'video_id': video[0],
                'title': video[1],
                'description': video[2],
                'channel': video[3],
                'channel_id': video[4],
                'thumbnail': video[5],
                'duration_seconds': video[6],
                'view_count': video[7],
                'like_count': video[8],
                'comment_count': video[9],
                'url': video[10],
                'comments_with_slang': [],
                'slang_comment_count': 0,
                'unique_slang_terms': []
            }
            
            # Parse comments if they exist
            if video[11]:  # comment_ids
                comment_ids = video[11].split(',')
                comment_texts = video[12].split(',')
                comment_authors = video[13].split(',')
                comment_likes = [int(x) if x else 0 for x in video[14].split(',')]
                comment_slang = video[15].split(',')
                
                comments_with_slang = []
                all_slang = set()
                
                for i, comment_id in enumerate(comment_ids):
                    if i < len(comment_texts):
                        slang_list = json.loads(comment_slang[i]) if comment_slang[i] else []
                        if slang_list:  # Only include comments with slang
                            comments_with_slang.append({
                                'comment_id': comment_id,
                                'text': comment_texts[i],
                                'author': comment_authors[i],
                                'like_count': comment_likes[i],
                                'detected_slang': slang_list
                            })
                            all_slang.update(slang_list)
                
                video_data['comments_with_slang'] = comments_with_slang
                video_data['slang_comment_count'] = len(comments_with_slang)
                video_data['unique_slang_terms'] = list(all_slang)
            
            result.append(video_data)
        
        conn.close()
        return result
    
    def get_cached_videos(self, topics: List[str], custom_slang: List[str], 
                      shorts_per_topic: int, comments_per_short: int) -> Optional[List[Dict]]:
        """
        Check if we have cached data for these parameters.
        Returns cached videos if found and not expired, None otherwise.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if we have recent cache for these parameters
        topics_json = json.dumps(topics)
        custom_slang_json = json.dumps(custom_slang)

        cursor.execute('''
            SELECT * FROM cache_metadata 
            WHERE topics = ? AND custom_slang = ? 
            AND shorts_per_topic = ? AND comments_per_short = ?
            AND expires_at > datetime('now')
            ORDER BY created_at DESC LIMIT 1
        ''', (topics_json, custom_slang_json, shorts_per_topic, comments_per_short))

        cache_entry = cursor.fetchone()
        if not cache_entry:
            conn.close()
            return None

        # Fetch videos
        cursor.execute('''
            SELECT * FROM videos
            ORDER BY created_at DESC
            LIMIT ?
        ''', (shorts_per_topic * len(topics),))
        videos = cursor.fetchall()

        if not videos:
            conn.close()
            return None

        result = []
        for video in videos:
            video_data = {
                'video_id': video[0],
                'title': video[1],
                'description': video[2],
                'channel': video[3],
                'channel_id': video[4],
                'thumbnail': video[5],
                'duration_seconds': video[6],
                'view_count': video[7],
                'like_count': video[8],
                'comment_count': video[9],
                'url': video[10],
                'comments_with_slang': [],
                'slang_comment_count': 0,
                'unique_slang_terms': []
            }

            # Fetch comments for this video
            cursor.execute('SELECT * FROM comments WHERE video_id = ?', (video[0],))
            comments = cursor.fetchall()

            comments_with_slang = []
            all_slang = set()

            for c in comments:
                slang_list = json.loads(c[8]) if c[8] else []
                if slang_list:  # Only include comments with slang
                    comments_with_slang.append({
                        'comment_id': c[0],
                        'text': c[2],
                        'author': c[3],
                        'like_count': c[5],
                        'detected_slang': slang_list
                    })
                    all_slang.update(slang_list)

            video_data['comments_with_slang'] = comments_with_slang
            video_data['slang_comment_count'] = len(comments_with_slang)
            video_data['unique_slang_terms'] = list(all_slang)

            result.append(video_data)

        conn.close()
        return result

    
    def clear_expired_cache(self):
        """Remove expired cache entries"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Delete expired cache metadata
        cursor.execute("DELETE FROM cache_metadata WHERE expires_at < datetime('now')")
        
        # Get video_ids that are no longer referenced
        cursor.execute('''
            SELECT v.video_id FROM videos v
            LEFT JOIN cache_metadata cm ON 1=1
            WHERE NOT EXISTS (
                SELECT 1 FROM comments c WHERE c.video_id = v.video_id
            ) AND NOT EXISTS (
                SELECT 1 FROM cache_metadata cm2 WHERE cm2.expires_at > datetime('now')
            )
        ''')
        
        orphaned_videos = cursor.fetchall()
        for video_id in orphaned_videos:
            cursor.execute("DELETE FROM videos WHERE video_id = ?", (video_id[0],))
            cursor.execute("DELETE FROM comments WHERE video_id = ?", (video_id[0],))
        
        conn.commit()
        conn.close()
