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
    
    # --- Consolidated and Corrected Reading Logic ---
    def get_cached_videos(self, topics: List[str], custom_slang: List[str], 
                          shorts_per_topic: int, comments_per_short: int) -> Optional[List[Dict]]:
        """
        Check if we have cached data for these parameters.
        Returns cached videos if found and not expired, None otherwise.
        (Consolidated logic for clarity and reduced SQL complexity.)
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
        # Fetching by ID is safer than GROUP_CONCAT which caused the previous crash.
        cursor.execute('''
            SELECT video_id, title, description, channel, channel_id, thumbnail, 
                   duration_seconds, view_count, like_count, comment_count, url
            FROM videos
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

            # Fetch comments for this video one by one
            cursor.execute('SELECT comment_id, text, author, like_count, detected_slang FROM comments WHERE video_id = ?', (video[0],))
            comments = cursor.fetchall()

            comments_with_slang = []
            all_slang = set()

            for c in comments:
                # c[4] is detected_slang (JSON string)
                slang_list = json.loads(c[4]) if c[4] else []
                if slang_list:  # Only include comments with slang
                    comments_with_slang.append({
                        'comment_id': c[0],
                        'text': c[1],
                        'author': c[2],
                        'like_count': c[3],
                        'detected_slang': slang_list
                    })
                    all_slang.update(slang_list)

            video_data['comments_with_slang'] = comments_with_slang
            video_data['slang_comment_count'] = len(comments_with_slang)
            video_data['unique_slang_terms'] = list(all_slang)

            result.append(video_data)

        conn.close()
        return result

    
    # --- MISSING WRITE METHOD ADDED ---
    def cache_videos(self, videos: List[Dict], topics: List[str], custom_slang: List[str],
                    shorts_per_topic: int, comments_per_short: int, cache_hours: int = 24):
        """
        Cache videos and comments to database
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear old cache for these exact parameters
        topics_json = json.dumps(topics)
        custom_slang_json = json.dumps(custom_slang)
        
        # Delete old metadata entry
        cursor.execute('''
            DELETE FROM cache_metadata 
            WHERE topics = ? AND custom_slang = ? AND shorts_per_topic = ? AND comments_per_short = ?
        ''', (topics_json, custom_slang_json, shorts_per_topic, comments_per_short))
        
        # Insert new cache metadata
        expires_at = datetime.now() + timedelta(hours=cache_hours)
        cursor.execute('''
            INSERT INTO cache_metadata 
            (topics, custom_slang, shorts_per_topic, comments_per_short, expires_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (topics_json, custom_slang_json, shorts_per_topic, comments_per_short, expires_at.strftime('%Y-%m-%d %H:%M:%S')))
        
        # Insert videos and comments
        for video in videos:
            video_id = video.get('video_id', '')
            
            # 1. Insert or replace video data
            cursor.execute('''
                INSERT OR REPLACE INTO videos 
                (video_id, title, description, channel, channel_id, thumbnail, 
                 duration_seconds, view_count, like_count, comment_count, url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                video_id,
                video.get('title', ''),
                video.get('description', ''),
                video.get('channel', ''),
                video.get('channel_id', ''),
                video.get('thumbnail', ''),
                video.get('duration_seconds', 0),
                video.get('view_count', 0),
                video.get('like_count', 0),
                video.get('comment_count', 0),
                video.get('url', '')
            ))
            
            # 2. Insert comments
            for comment in video.get('comments_with_slang', []):
                cursor.execute('''
                    INSERT OR REPLACE INTO comments 
                    (comment_id, video_id, text, author, author_channel_url, 
                     like_count, published_at, reply_count, detected_slang)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    comment.get('comment_id', ''),
                    video_id,
                    comment.get('text', ''),
                    comment.get('author', ''),
                    comment.get('author_channel_url', ''),
                    comment.get('like_count', 0),
                    comment.get('published_at', ''),
                    comment.get('reply_count', 0),
                    json.dumps(comment.get('detected_slang', []))
                ))
        
        conn.commit()
        conn.close()

    def get_any_cached_videos(self, limit: int = 20) -> Optional[List[Dict]]:
        """
        Fallback method to get ANY cached videos regardless of topics/parameters.
        Used when YouTube API quota is exhausted.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get most recent videos
        cursor.execute('''
            SELECT video_id, title, description, channel, channel_id, thumbnail,
                   duration_seconds, view_count, like_count, comment_count, url
            FROM videos
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
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
            cursor.execute('SELECT comment_id, text, author, like_count, detected_slang FROM comments WHERE video_id = ?', (video[0],))
            comments = cursor.fetchall()

            comments_with_slang = []
            all_slang = set()

            for c in comments:
                slang_list = json.loads(c[4]) if c[4] else []
                if slang_list:
                    comments_with_slang.append({
                        'comment_id': c[0],
                        'text': c[1],
                        'author': c[2],
                        'like_count': c[3],
                        'detected_slang': slang_list
                    })
                    all_slang.update(slang_list)

            video_data['comments_with_slang'] = comments_with_slang
            video_data['slang_comment_count'] = len(comments_with_slang)
            video_data['unique_slang_terms'] = list(all_slang)

            result.append(video_data)

        conn.close()
        return result

    # --- Clear Expired Cache Logic (Unchanged) ---
    def clear_expired_cache(self):
        """Remove expired cache entries"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Delete expired cache metadata
        cursor.execute("DELETE FROM cache_metadata WHERE expires_at < datetime('now')")

        # This logic is complex and often unnecessary unless space is critical,
        # but kept here for function signature completeness.
        # It attempts to delete videos/comments that are no longer referenced by any cache_metadata.
        cursor.execute('''
            DELETE FROM videos WHERE video_id IN (
                SELECT v.video_id FROM videos v
                LEFT JOIN comments c ON v.video_id = c.video_id
                WHERE c.video_id IS NULL AND NOT EXISTS (
                    SELECT 1 FROM cache_metadata WHERE expires_at > datetime('now')
                )
            )
        ''')

        conn.commit()
        conn.close()