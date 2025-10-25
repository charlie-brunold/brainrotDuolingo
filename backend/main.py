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


# Load API keys
load_dotenv()
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY') or 'AIzaSyCq_t-V6P38IQBVK2v0Wk4SdoU5l2Ch15o'
GROQ_API_KEY = os.getenv('GROQ_API_KEY') or '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'

if not YOUTUBE_API_KEY:
    raise ValueError("YOUTUBE_API_KEY missing")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY missing")


# Initialize FastAPI and services
app = FastAPI()
fetcher = YouTubeShortsSlangFetcher(YOUTUBE_API_KEY)
groq_evaluator = GroqCommentEvaluator(GROQ_API_KEY)
slang_discovery = SlangDiscovery(GROQ_API_KEY)

# Sync fetcher's slang_terms with discovery database
fetcher.slang_terms = slang_discovery.get_all_slang_terms()

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


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚀 Starting Slang Learning Backend")
    print("="*60)
    print(f"📚 Loaded {len(slang_discovery.slang_database)} slang terms")
    print(f"🎯 Fetcher configured with {len(fetcher.slang_terms)} terms")
    print("="*60 + "\n")
    uvicorn.run(app, host="127.0.0.1", port=3001, reload=True)
    