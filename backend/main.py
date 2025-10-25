# main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from youtube_fetcher import YouTubeShortsSlangFetcher
from groq_evaluator import GroqCommentEvaluator
from slang_discovery import SlangDiscovery
from dotenv import load_dotenv
import os
from typing import List, Optional
import json
from database import VideoDatabase

# CACHE_FILE = "cached_shorts.json"

# def load_cache():
#     global cached_shorts
#     if os.path.exists(CACHE_FILE):
#         try:
#             with open(CACHE_FILE, "r", encoding="utf-8") as f:
#                 cached_shorts = json.load(f)
#             print(f"✅ Loaded {len(cached_shorts)} cached videos from {CACHE_FILE}")
#         except Exception as e:
#             print("⚠️ Failed to load cache:", e)

# def save_cache():
#     try:
#         with open(CACHE_FILE, "w", encoding="utf-8") as f:
#             json.dump(cached_shorts, f, indent=2)
#         print(f"💾 Saved {len(cached_shorts)} videos to cache")
#     except Exception as e:
#         print("⚠️ Failed to save cache:", e)


# Try to import groq_evaluator, but make it optional
try:
    from groq_evaluator import GroqCommentEvaluator
    GROQ_AVAILABLE = True
except ImportError:
    print("⚠️ Groq evaluator not available - AI features will be disabled")
    GROQ_AVAILABLE = False

# Load API keys
load_dotenv()
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY') 
GROQ_API_KEY = os.getenv('GROQ_API_KEY') 

if not YOUTUBE_API_KEY:
    raise ValueError("YOUTUBE_API_KEY missing")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY missing")


# Initialize FastAPI and services
app = FastAPI()
fetcher = YouTubeShortsSlangFetcher(YOUTUBE_API_KEY)
groq_evaluator = GroqCommentEvaluator(GROQ_API_KEY)
slang_discovery = SlangDiscovery(GROQ_API_KEY)
db = VideoDatabase()

# Sync fetcher's slang_terms with discovery database
fetcher.slang_terms = slang_discovery.get_all_slang_terms()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# cached_shorts = []

# Request models
class RefreshRequest(BaseModel):
    topics: Optional[List[str]] = ["gaming", "food review", "funny moments", "dance", "pets"]

class DiscoverRequest(BaseModel):
    topics: List[str]
    auto_approve: bool = False

class VideoConfig(BaseModel):
    topics: List[str] = ["gaming", "food review", "funny moments", "dance", "pets"]
    shorts_per_topic: int = 5
    comments_per_short: int = 30
    # Add an optional custom_slang field if your client might send it
    custom_slang: List[str] = []

# cached_shorts = []
# load_cache()

# ============================================================================
# GROQ AI EVALUATION REQUEST/RESPONSE MODELS
# ============================================================================

class EvaluateRequest(BaseModel):
    videoTitle: str
    videoDescription: str
    userComment: str
    targetLanguage: str
    videoLikeCount: int
    availableSlang: List[str] = []  # Slang terms available in the video

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
    availableSlang: List[str] = []  # Slang available in the video

class AIResponse(BaseModel):
    aiComment: str
    authorName: str
    likes: int

class RespondResponse(BaseModel):
    responses: List[AIResponse]

class SlangBreakdownItem(BaseModel):
    term: str
    definition: str
    usage: str

class ExplainCommentRequest(BaseModel):
    commentText: str
    videoTitle: str
    videoDescription: str
    detectedSlang: List[str] = []

class ExplainCommentResponse(BaseModel):
    translation: str
    slangBreakdown: List[SlangBreakdownItem]

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
def home():
    return {
        "message": "Backend running with auto slang discovery and SQLite cache!",
        "slang_terms_loaded": len(fetcher.slang_terms),
    }

@app.post("/api/clear-cache")
def clear_cache():
    """Clear expired cache entries from the SQLite database."""
    try:
        db.clear_expired_cache()
        return {"message": "Expired cache cleared successfully from database."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")

@app.get("/api/cache-stats")
def cache_stats():
    """Get cache statistics from the SQLite database."""
    try:
        # NOTE: This implementation relies on the database being initialized as 'db'
        conn = db.init_database() # Re-use the connection method if possible, otherwise connect directly
        
        # Use a fresh connection for the stats retrieval
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


# main.py (Replacing the previous consolidated endpoint)

@app.get("/api/videos")
def get_videos_db_get(
    topics: List[str] = ["gaming", "food review", "funny moments", "dance", "pets"],
    shorts_per_topic: int = 5,
    comments_per_short: int = 30
):
    """Fetches videos using Query Parameters (GET)"""
    # Create the config object from query parameters for consistency
    config = VideoConfig(
        topics=topics, 
        shorts_per_topic=shorts_per_topic, 
        comments_per_short=comments_per_short
    )
    return fetch_and_cache_videos(config)

@app.post("/api/videos")
def get_videos_db_post(config: VideoConfig):
    """Fetches videos using a JSON Request Body (POST)"""
    return fetch_and_cache_videos(config)

# main.py (Define this utility function outside of the endpoints)

def fetch_and_cache_videos(config: VideoConfig):
    
    # 1. Prepare parameters for cache lookup
    custom_slang = config.custom_slang 
    
    # 2. Check database cache
    cached_data = db.get_cached_videos(
        topics=config.topics,
        custom_slang=custom_slang,
        shorts_per_topic=config.shorts_per_topic,
        comments_per_short=config.comments_per_short
    )
    
    if cached_data:
        print(f"✅ Returning {len(cached_data)} cached videos from SQLite")
        return cached_data

    # 3. If no cache, fetch new data
    print(f"🔄 Fetching fresh data from YouTube API for topics: {config.topics}")
    shorts_data = fetcher.fetch_shorts(
        topics=config.topics,
        shorts_per_topic=config.shorts_per_topic,
        comments_per_short=config.comments_per_short
    )
    
    # 4. Save cache
    db.cache_videos(
        videos=shorts_data,
        topics=config.topics,
        custom_slang=custom_slang,
        shorts_per_topic=config.shorts_per_topic,
        comments_per_short=config.comments_per_short,
        cache_hours=24
    )
    print(f"💾 Cached {len(shorts_data)} videos to SQLite database")

    return shorts_data

@app.post("/api/refresh")
def refresh_videos(request: RefreshRequest = None):
    """Refresh videos, discover new slang, and cache results in the database."""
    
    # ... (Discovery and fetching logic remains the same) ...

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
        shorts_data = fetcher.fetch_shorts(topics, shorts_per_topic=5, comments_per_short=30)
    
    # Cache the final results using the database instead of JSON
    db.cache_videos(
        videos=shorts_data,
        topics=topics,
        custom_slang=[], 
        shorts_per_topic=5,
        comments_per_short=30,
        cache_hours=24
    )
    print(f"💾 Refreshed {len(shorts_data)} videos in SQLite database")

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
        )
    return {
        "term": term,
        **info
    }


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

# Stage 1: Evaluate user comment and return score with social validation
@app.post("/api/evaluate", response_model=EvaluateResponse)
def evaluate_comment(request: EvaluateRequest):
    """
    Evaluate a user's comment on a video.

    Returns:
        - score (0-100): Overall evaluation score (capped at 50 if no slang used)
        - grammarScore, contextScore, naturalnessScore: Breakdown
        - likes: Percentage of video's likes (realistic social validation)
        - correction: Corrected version of comment
        - mistakes: Array of identified errors
        - goodParts: Array of positive aspects
    """
    try:
        evaluation = groq_evaluator.evaluate_comment(
            video_title=request.videoTitle,
            video_description=request.videoDescription,
            user_comment=request.userComment,
            target_language=request.targetLanguage,
            video_like_count=request.videoLikeCount,
            available_slang=request.availableSlang
        )
        return evaluation
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation error: {str(e)}")


# Stage 2: Generate multiple AI responses with roast-with-love personalities
@app.post("/api/respond", response_model=RespondResponse)
def generate_ai_response(request: RespondRequest):
    """
    Generate multiple Gen Z style AI responses to user's comment.
    Number of responses scales with comment quality (1-5 responses based on score).

    Returns:
        - responses: List of 1-5 AI responses (score-based), each with:
            - aiComment: TikTok-style roast-with-love feedback (tone matches score tier)
            - authorName: Groq-generated Gen Z username
            - likes: Random engagement count (10-500)
    """
    try:
        responses = groq_evaluator.generate_multiple_responses(
            user_comment=request.userComment,
            score=request.score,
            mistakes=request.mistakes,
            correction=request.correction,
            video_title=request.videoTitle,
            target_language=request.targetLanguage,
            available_slang=request.availableSlang
        )
        return {"responses": responses}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Response generation error: {str(e)}")

# Stage 3: Explain YouTube comments with slang translations
@app.post("/api/explain-comment", response_model=ExplainCommentResponse)
def explain_comment(request: ExplainCommentRequest):
    """
    Explain a YouTube comment by translating it to simpler language
    and breaking down each slang term.

    Returns:
        - translation: The comment rewritten in simple language without slang
        - slangBreakdown: Array of objects with term, definition, and usage
    """
    if not groq_evaluator:
        raise HTTPException(status_code=503, detail="AI response service not available. Please check Groq API key.")
    
    try:
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
    
