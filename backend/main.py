# main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from youtube_fetcher import YouTubeShortsSlangFetcher
<<<<<<< Updated upstream
<<<<<<< Updated upstream
from groq_evaluator import GroqCommentEvaluator
from slang_discovery import SlangDiscovery
=======
from database import VideoDatabase
>>>>>>> Stashed changes
=======
from database import VideoDatabase
>>>>>>> Stashed changes
from dotenv import load_dotenv
import os
from typing import List, Optional
import json

CACHE_FILE = "cached_shorts.json"

def load_cache():
    global cached_shorts
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cached_shorts = json.load(f)
            print(f"✅ Loaded {len(cached_shorts)} cached videos from {CACHE_FILE}")
        except Exception as e:
            print("⚠️ Failed to load cache:", e)

def save_cache():
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cached_shorts, f, indent=2)
        print(f"💾 Saved {len(cached_shorts)} videos to cache")
    except Exception as e:
        print("⚠️ Failed to save cache:", e)


# Try to import groq_evaluator, but make it optional
try:
    from groq_evaluator import GroqCommentEvaluator
    GROQ_AVAILABLE = True
except ImportError:
    print("⚠️ Groq evaluator not available - AI features will be disabled")
    GROQ_AVAILABLE = False

# Try to import groq_evaluator, but make it optional
try:
    from groq_evaluator import GroqCommentEvaluator
    GROQ_AVAILABLE = True
except ImportError:
    print("⚠️ Groq evaluator not available - AI features will be disabled")
    GROQ_AVAILABLE = False

# Load API keys
load_dotenv()
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY') or 'AIzaSyCq_t-V6P38IQBVK2v0Wk4SdoU5l2Ch15o'
GROQ_API_KEY = os.getenv('GROQ_API_KEY') or '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'

if not YOUTUBE_API_KEY:
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    raise ValueError("YOUTUBE_API_KEY missing")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY missing")

=======
    raise ValueError("YOUTUBE_API_KEY missing in .env file. Please add your YouTube API key.")
>>>>>>> Stashed changes
=======
    raise ValueError("YOUTUBE_API_KEY missing in .env file. Please add your YouTube API key.")
>>>>>>> Stashed changes

# Initialize FastAPI and services
app = FastAPI()
fetcher = YouTubeShortsSlangFetcher(YOUTUBE_API_KEY)
<<<<<<< Updated upstream
<<<<<<< Updated upstream
groq_evaluator = GroqCommentEvaluator(GROQ_API_KEY)
slang_discovery = SlangDiscovery(GROQ_API_KEY)

# Sync fetcher's slang_terms with discovery database
fetcher.slang_terms = slang_discovery.get_all_slang_terms()
=======
=======
>>>>>>> Stashed changes
db = VideoDatabase()

# Initialize Groq evaluator only if available
if GROQ_AVAILABLE and GROQ_API_KEY:
    groq_evaluator = GroqCommentEvaluator(GROQ_API_KEY)
    print("✅ Groq evaluator initialized")
else:
    groq_evaluator = None
    print("⚠️ Groq evaluator not available - AI comment evaluation disabled")
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

cached_shorts = []

# Request models
class RefreshRequest(BaseModel):
    topics: Optional[List[str]] = ["gaming", "food review", "funny moments", "dance", "pets"]

class DiscoverRequest(BaseModel):
    topics: List[str]
    auto_approve: bool = False

cached_shorts = []
load_cache()

@app.get("/")
def home():
    return {
        "message": "Backend running with auto slang discovery!",
        "slang_terms_loaded": len(fetcher.slang_terms),
        "cached_videos": len(cached_shorts)
    }

@app.post("/api/clear-cache")
def clear_cache():
    """Clear expired cache entries"""
    try:
        db.clear_expired_cache()
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")

@app.get("/api/cache-stats")
def cache_stats():
    """Get cache statistics"""
    try:
        import sqlite3
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        # Get video count
        cursor.execute("SELECT COUNT(*) FROM videos")
        video_count = cursor.fetchone()[0]
        
        # Get comment count
        cursor.execute("SELECT COUNT(*) FROM comments")
        comment_count = cursor.fetchone()[0]
        
        # Get cache entries
        cursor.execute("SELECT COUNT(*) FROM cache_metadata")
        cache_entries = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "videos_cached": video_count,
            "comments_cached": comment_count,
            "cache_entries": cache_entries,
            "database_size": os.path.getsize(db.db_path) if os.path.exists(db.db_path) else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cache stats: {str(e)}")

@app.post("/api/clear-cache")
def clear_cache():
    """Clear expired cache entries"""
    try:
        db.clear_expired_cache()
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")

@app.get("/api/cache-stats")
def cache_stats():
    """Get cache statistics"""
    try:
        import sqlite3
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        # Get video count
        cursor.execute("SELECT COUNT(*) FROM videos")
        video_count = cursor.fetchone()[0]
        
        # Get comment count
        cursor.execute("SELECT COUNT(*) FROM comments")
        comment_count = cursor.fetchone()[0]
        
        # Get cache entries
        cursor.execute("SELECT COUNT(*) FROM cache_metadata")
        cache_entries = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "videos_cached": video_count,
            "comments_cached": comment_count,
            "cache_entries": cache_entries,
            "database_size": os.path.getsize(db.db_path) if os.path.exists(db.db_path) else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cache stats: {str(e)}")


# main.py - inside get_videos (around line 28)
@app.get("/api/videos")
def get_videos():
    global cached_shorts
    if cached_shorts:
        return cached_shorts
    # Increased number of topics for more variety
    topics = ["gaming", "food review", "funny moments", "dance", "pets"] 
    # Pass topics to the fetcher
    shorts_data = fetcher.fetch_shorts(topics) 
    cached_shorts = shorts_data
    return shorts_data
# ...

# main.py - inside get_videos (around line 28)
@app.get("/api/videos")
def get_videos():
    global cached_shorts
    if cached_shorts:
        return cached_shorts
    # Increased number of topics for more variety
    topics = ["gaming", "food review", "funny moments", "dance", "pets"] 
    # Pass topics to the fetcher
    shorts_data = fetcher.fetch_shorts(topics) 
    cached_shorts = shorts_data
    return shorts_data
# ...

<<<<<<< Updated upstream
@app.get("/api/videos")
@app.post("/api/videos")  # Support both GET and POST
def get_videos():
    """Get cached videos or fetch new ones"""
    global cached_shorts
    
    if cached_shorts:
        return cached_shorts
    
    # Make sure we have latest slang
    fetcher.slang_terms = slang_discovery.get_all_slang_terms()
    
    topics = ["gaming", "food review", "funny moments", "dance", "pets"] 
    shorts_data = fetcher.fetch_shorts(topics, shorts_per_topic=5) 
    cached_shorts = shorts_data
    save_cache()
    return shorts_data


@app.post("/api/refresh")
def refresh_videos(request: RefreshRequest = None):
    """Refresh videos AND automatically discover new slang"""
    global cached_shorts
    
    # Handle both body and default
    topics = request.topics if request else ["gaming", "food review", "funny moments", "dance", "pets"]
    
    print(f"\n🔄 Refreshing with topics: {topics}")
    
    # Update fetcher with current slang database
    fetcher.slang_terms = slang_discovery.get_all_slang_terms()
    print(f"📚 Current slang database: {len(fetcher.slang_terms)} terms")
    
    # Fetch videos with current slang
    shorts_data = fetcher.fetch_shorts(topics, shorts_per_topic=5, comments_per_short=30)
    print(f"📹 Fetched {len(shorts_data)} shorts")
    
    # Collect ALL comments for discovery
    all_comments = []
    for short in shorts_data:
        # Get the comments that were already fetched (they have slang)
        comments_with_slang = short.get('comments_with_slang', [])
        all_comments.extend(comments_with_slang)
    
    print(f"💬 Collected {len(all_comments)} comments for analysis")
    
    # Discover new slang
    new_slang = []
    if len(all_comments) > 10:
        print("🤖 Running AI slang discovery...")
        new_slang = slang_discovery.discover_new_slang(
            all_comments, 
            auto_approve=True
        )
    
    # If we found new slang, re-fetch to include them
    if new_slang:
        print(f"✨ Discovered {len(new_slang)} new terms! Re-fetching...")
        fetcher.slang_terms = slang_discovery.get_all_slang_terms()
        shorts_data = fetcher.fetch_shorts(topics, shorts_per_topic=5)
    
    cached_shorts = shorts_data
    save_cache()
    return {
        "videos": shorts_data,
        "new_slang_discovered": [
            {
                "term": s['term'],
                "definition": s['definition'],
                "category": s['category'],
                "example": s['example']
            } for s in new_slang
        ],
        "total_slang_terms": len(fetcher.slang_terms)
    }


@app.get("/api/slang")
def get_all_slang():
    """Get all known slang terms with definitions"""
    slang_db = slang_discovery.slang_database
    return {
        "total_terms": len(slang_db),
        "terms": [
            {
                "term": term,
                "definition": info.get('definition', ''),
                "category": info.get('category', 'descriptive'),
                "example": info.get('example', '')
            }
            for term, info in slang_db.items()
        ]
    }


@app.get("/api/slang/{term}")
def get_slang_definition(term: str):
    """Get definition for a specific slang term"""
    info = slang_discovery.get_slang_info(term)
    if not info:
        raise HTTPException(
            status_code=404, 
            detail=f"Slang term '{term}' not found"
=======
# Request model for user configuration
class UserConfig(BaseModel):
    topics: List[str]
    custom_slang: List[str] = []
    shorts_per_topic: int = 10
    comments_per_short: int = 50

# main.py - inside refresh_videos (around line 36)
@app.post("/api/refresh")
def refresh_videos(topics: List[str] = ["gaming", "food review", "funny moments", "dance", "pets"]):
    global cached_shorts
    # Pass topics to the fetcher
    shorts_data = fetcher.fetch_shorts(topics)
    cached_shorts = shorts_data
    return shorts_data

# New endpoint that accepts user configuration with custom slang
@app.post("/api/videos")
def get_videos_with_config(config: UserConfig):
    try:
        # First, check database cache
        cached_data = db.get_cached_videos(
            topics=config.topics,
            custom_slang=config.custom_slang,
            shorts_per_topic=config.shorts_per_topic,
            comments_per_short=config.comments_per_short
        )
        
        if cached_data:
            print(f"✅ Returning {len(cached_data)} cached videos")
            return cached_data
        
        # Fetch from YouTube API
        print(f"🔄 Fetching fresh data from YouTube API for topics: {config.topics}")
        shorts_data = fetcher.fetch_shorts(
            topics=config.topics,
            shorts_per_topic=config.shorts_per_topic,
            comments_per_short=config.comments_per_short,
            custom_slang=config.custom_slang
        )
        
        # Cache the results for future use
        if shorts_data:
            db.cache_videos(
                videos=shorts_data,
                topics=config.topics,
                custom_slang=config.custom_slang,
                shorts_per_topic=config.shorts_per_topic,
                comments_per_short=config.comments_per_short,
                cache_hours=24  # Cache for 24 hours
            )
            print(f"💾 Cached {len(shorts_data)} videos to database")
        
        return shorts_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching videos: {str(e)}")

def generate_mock_data(config: UserConfig):
    """Generate mock video data for testing"""
    import random
    import string
    
    # Combine default slang with custom slang
    all_slang = {
        'fr', 'ngl', 'tbh', 'smh', 'imo', 'lol', 'lmao', 
        'bruh', 'bet', 'bussin', 'sheesh', 'sigma', 'lit', 
        'lowkey', 'highkey', 'cap', 'nocap', 'vibe', 'vibes',
        'slay', 'goat', 'savage', 'flex', 'sus', 'mid',
        'w', 'l', 'ratio', 'fam', 'stan', 'simp', 'based',
        'yeet', 'slaps', 'valid', 'mood', 'hits different'
    }
    if config.custom_slang:
        all_slang.update(map(str.lower, config.custom_slang))
    
    # Sample video titles and descriptions
    video_templates = {
        'gaming': [
            ("Epic Gaming Moment That Went Viral", "This gaming clip is absolutely insane! The reactions are priceless."),
            ("Gamer Reacts to Impossible Challenge", "You won't believe what happened in this gaming session!"),
            ("Pro Gamer Shows Secret Technique", "This technique changed everything for me in this game.")
        ],
        'cooking': [
            ("5-Minute Recipe That Actually Works", "This recipe is so simple but tastes amazing!"),
            ("Cooking Hack That Will Blow Your Mind", "I can't believe I didn't know this trick before!"),
            ("Failed Recipe Turned Into Success", "What started as a disaster became my favorite dish!")
        ],
        'funny': [
            ("Funniest Moment Caught on Camera", "I was laughing so hard I couldn't breathe!"),
            ("Prank Gone Wrong (But Still Funny)", "This prank backfired in the best way possible!"),
            ("Comedy Gold That You Need to See", "This is the funniest thing I've seen all week!")
        ]
    }
    
    mock_videos = []
    video_id = 1
    
    for topic in config.topics[:3]:  # Limit to 3 topics for testing
        templates = video_templates.get(topic, [("Amazing {topic} Content", "This {topic} video is incredible!")])
        
        for i in range(min(config.shorts_per_topic, 3)):  # Limit to 3 videos per topic
            # Generate realistic YouTube video ID
            video_id_str = ''.join(random.choices(string.ascii_letters + string.digits, k=11))
            
            # Pick a template or create generic one
            if templates:
                title_template, desc_template = random.choice(templates)
                title = title_template.replace('{topic}', topic)
                description = desc_template.replace('{topic}', topic)
            else:
                title = f"Amazing {topic} Video #{i+1}"
                description = f"This is a great {topic} video with lots of slang!"
            
            # Generate mock comments with slang
            comments_with_slang = []
            comment_templates = [
                "This is so {slang} {slang}!",
                "Bro this {slang} content fr",
                "No cap this is {slang}",
                "This {slang} {slang} content hits different",
                "Sheesh this is {slang}",
                "This {slang} {slang} is bussin",
                "Lowkey this {slang} content is fire"
            ]
            
            for j in range(min(config.comments_per_short, 8)):  # Limit to 8 comments
                slang_used = random.sample(list(all_slang), random.randint(1, 2))
                template = random.choice(comment_templates)
                comment_text = template.format(slang=random.choice(slang_used))
                
                comments_with_slang.append({
                    'comment_id': f"comment_{video_id_str}_{j}",
                    'text': comment_text,
                    'author': f"User{j+1}",
                    'author_channel_url': f"https://youtube.com/user{j+1}",
                    'like_count': random.randint(0, 500),
                    'published_at': "2024-01-01T00:00:00Z",
                    'reply_count': random.randint(0, 10),
                    'detected_slang': slang_used
                })
            
            # Collect all unique slang terms
            all_slang_in_video = set()
            for comment in comments_with_slang:
                all_slang_in_video.update(comment['detected_slang'])
            
            mock_videos.append({
                'video_id': video_id_str,
                'title': title,
                'description': description,
                'channel': f"{topic.title()}Channel",
                'channel_id': f"UC{''.join(random.choices(string.ascii_letters + string.digits, k=22))}",
                'thumbnail': f"https://i.ytimg.com/vi/{video_id_str}/maxresdefault.jpg",
                'duration_seconds': random.randint(15, 60),
                'view_count': random.randint(10000, 5000000),
                'like_count': random.randint(1000, 500000),
                'comment_count': random.randint(100, 10000),
                'url': f"https://www.youtube.com/shorts/{video_id_str}",
                'comments_with_slang': comments_with_slang,
                'slang_comment_count': len(comments_with_slang),
                'unique_slang_terms': list(all_slang_in_video)
            })
            video_id += 1
    
    return mock_videos


# ============================================================================
# GROQ AI EVALUATION ENDPOINTS
# ============================================================================

# Request/Response Models
class EvaluateRequest(BaseModel):
    videoTitle: str
    videoDescription: str
    userComment: str
    targetLanguage: str
    videoViewCount: int

class EvaluateResponse(BaseModel):
    score: int
    grammarScore: int
    contextScore: int
    naturalnessScore: int
    likes: int
    correction: str
    mistakes: List[str]
    goodParts: List[str]

class RespondRequest(BaseModel):
    userComment: str
    score: int
    mistakes: List[str]
    correction: str
    videoTitle: str
    targetLanguage: str

class RespondResponse(BaseModel):
    aiComment: str
    authorName: str
    likes: int


# Stage 1: Evaluate user comment and return score with social validation
@app.post("/api/evaluate", response_model=EvaluateResponse)
def evaluate_comment(request: EvaluateRequest):
    """
    Evaluate a user's comment on a video.

    Returns:
        - score (0-100): Overall evaluation score
        - grammarScore, contextScore, naturalnessScore: Breakdown
        - likes: View-based percentage likes (social validation)
        - correction: Corrected version of comment
        - mistakes: Array of identified errors
        - goodParts: Array of positive aspects
    """
    if not groq_evaluator:
        raise HTTPException(status_code=503, detail="AI evaluation service not available. Please check Groq API key.")
    
    try:
        evaluation = groq_evaluator.evaluate_comment(
            video_title=request.videoTitle,
            video_description=request.videoDescription,
            user_comment=request.userComment,
            target_language=request.targetLanguage,
            video_view_count=request.videoViewCount
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        )
    return {
        "term": term,
        **info
    }


<<<<<<< Updated upstream
@app.post("/api/discover-slang")
def manual_discovery(request: DiscoverRequest):
    """Manually trigger slang discovery"""
    print(f"\n🔍 Manual discovery for: {request.topics}")
    
    # Fetch videos
    shorts_data = fetcher.fetch_shorts(request.topics)
    
    # Collect comments
    all_comments = []
    for short in shorts_data:
        all_comments.extend(short.get('comments_with_slang', []))
    
    print(f"💬 Analyzing {len(all_comments)} comments...")
    
    # Discover
    new_slang = slang_discovery.discover_new_slang(
        all_comments, 
        auto_approve=request.auto_approve
    )
    
    return {
        "discovered": len(new_slang),
        "terms": new_slang,
        "auto_approved": request.auto_approve
    }


@app.delete("/api/slang/{term}")
def delete_slang(term: str):
    """Remove a slang term"""
    if term.lower() not in slang_discovery.slang_database:
        raise HTTPException(status_code=404, detail=f"Term '{term}' not found")
    
    del slang_discovery.slang_database[term.lower()]
    slang_discovery.save_slang_database()
    fetcher.slang_terms = slang_discovery.get_all_slang_terms()
    
    return {"message": f"Deleted '{term}'"}


<<<<<<< Updated upstream
@app.get("/api/stats")
def get_stats():
    """Get system statistics"""
    from collections import Counter
    
    categories = [
        info.get('category', 'unknown') 
        for info in slang_discovery.slang_database.values()
    ]
    category_counts = dict(Counter(categories))
    
    return {
        "cached_videos": len(cached_shorts),
        "total_slang_terms": len(slang_discovery.slang_database),
        "slang_by_category": category_counts,
        "most_common_category": max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else None
    }



# Stage 3: Explain YouTube comments with slang translations
@app.post("/api/explain-comment", response_model=ExplainCommentResponse)
def explain_comment(request: ExplainCommentRequest):
    """
    Explain a YouTube comment by translating it to simpler language
    and breaking down each slang term.

    Returns:
        - translation: The comment rewritten in simple language without slang
        - slangBreakdown: Array of objects with term, definition, and usage
=======
=======
>>>>>>> Stashed changes
# Stage 2: Generate AI response with roast-with-love personality
@app.post("/api/respond", response_model=RespondResponse)
def generate_ai_response(request: RespondRequest):
    """
    Generate a Gen Z style AI response to user's comment.

    Returns:
        - aiComment: TikTok-style roast-with-love feedback
        - authorName: Random AI coach personality name
        - likes: Random engagement count (10-500)
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    """
    if not groq_evaluator:
        raise HTTPException(status_code=503, detail="AI response service not available. Please check Groq API key.")
    
    try:
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        explanation = groq_evaluator.explain_comment(
            comment_text=request.commentText,
            video_title=request.videoTitle,
            video_description=request.videoDescription,
            detected_slang=request.detectedSlang
        )
        return explanation
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚀 Starting Slang Learning Backend")
    print("="*60)
    print(f"📚 Loaded {len(slang_discovery.slang_database)} slang terms")
    print(f"🎯 Fetcher configured with {len(fetcher.slang_terms)} terms")
    print("="*60 + "\n")
    uvicorn.run(app, host="127.0.0.1", port=3001, reload=True)
    
=======
=======
>>>>>>> Stashed changes
        response = groq_evaluator.generate_response(
            user_comment=request.userComment,
            score=request.score,
            mistakes=request.mistakes,
            correction=request.correction,
            video_title=request.videoTitle,
            target_language=request.targetLanguage
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Response generation error: {str(e)}")
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
