import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from youtube_fetcher import YouTubeShortsSlangFetcher
from groq_evaluator import GroqCommentEvaluator
from slang_discovery import SlangDiscovery
from database import VideoDatabase
from dotenv import load_dotenv
import os
import re
from typing import List, Optional, Dict
from collections import defaultdict, Counter
import json
import random  # <-- NEW: Import for shuffling lists
import time # <-- NEW: Import for time.sleep in retry logic
import base64  # <-- NEW: For encoding audio to base64
from youtube_transcript_api import YouTubeTranscriptApi  # <-- NEW: For fetching transcripts

# ============================================================================
# 3. REQUEST/RESPONSE MODELS
# ============================================================================

# General Request Models
class DiscoverRequest(BaseModel):
    topics: List[str]
    auto_approve: bool = False

class VideoConfig(BaseModel):
    topics: List[str] = ["gaming", "food review", "funny moments", "dance", "pets"]
    shorts_per_topic: int = 15 
    comments_per_short: int = 30
    custom_slang: List[str] = []

# AI Evaluation Models (Abbreviated for brevity, assuming standard structure)
class EvaluateRequest(BaseModel):
    videoTitle: str
    videoDescription: str
    userComment: str
    targetLanguage: str
    videoLikeCount: int
    availableSlang: List[str] = [] 

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
    availableSlang: List[str] = []

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

class TranslateVideoRequest(BaseModel):
    video_id: str
    target_language: str = "Spanish"  # Default to Spanish

class TranscriptSegment(BaseModel):
    text: str
    start: float
    duration: float

class TranslateVideoResponse(BaseModel):
    video_id: str
    target_language: str
    original_transcript: List[TranscriptSegment]
    translated_text: str
    audio_base64: str
    audio_format: str


# ============================================================================
# 1. HELPER FUNCTIONS
# ============================================================================

def extract_slang_candidates_with_context(all_comments: List[Dict]) -> Dict[str, List[str]]:
    """
    INJECTED HELPER FUNCTION: This logic replaces the external call and is used 
    by the manual_discovery endpoint to filter comments locally before AI verification.
    """
    
    candidate_counts = Counter()
    candidate_context = defaultdict(list)
    
    # Use existing slang for fast lookup and exclusion
    existing_slang = slang_discovery.get_all_slang_terms()
    approved_slang = set(term.lower() for term in existing_slang)
    
    for comment_data in all_comments:
        text = comment_data.get('text', '').lower()
        
        # Simple tokenization for words (alphanumeric only)
        words = re.findall(r'\b[a-z0-9]+\b', text)
        
        # Check single words
        for word in words:
            if len(word) > 2 and word not in approved_slang:
                candidate_counts[word] += 1
                if len(candidate_context[word]) < 3: # Store up to 3 context examples
                    candidate_context[word].append(text)

        # Check two-word phrases (bigrams)
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i+1]}"
            if phrase not in approved_slang and len(phrase) > 4:
                candidate_counts[phrase] += 1
                if len(candidate_context[phrase]) < 3:
                    candidate_context[phrase].append(text)

    # Filter candidates based on frequency (heuristic: must appear in at least 3 comments)
    MIN_FREQUENCY = 3 
    final_candidates = {}
    
    for candidate, count in candidate_counts.items():
        if count >= MIN_FREQUENCY:
            # Final check to avoid sending overly long phrases to AI
            if candidate not in approved_slang and len(candidate.split()) <= 2:
                final_candidates[candidate] = candidate_context[candidate]

    return final_candidates

def fetch_and_cache_videos(config: VideoConfig, slang_only: bool = False, last_video_id: Optional[str] = None):
    """
    Unified function to check cache, fetch videos from YouTube, and save results to DB.
    """
    
    # 1. Prepare parameters for cache lookup
    custom_slang = config.custom_slang 
    
    # Cache Busting logic
    shorts_per_topic_base = config.shorts_per_topic
    shorts_per_topic = shorts_per_topic_base + random.choice([0, 0, 1, 1, 2, 2])
    
    # 2. Check database cache (read operation)
    cached_data = db.get_cached_videos(
        topics=config.topics,
        custom_slang=custom_slang,
        shorts_per_topic=shorts_per_topic, 
        comments_per_short=config.comments_per_short
    )
    
    final_videos = []
    priority_video = None
    
    # Handle cache hit
    if cached_data:
        # Filter for slang_only if requested
        if slang_only:
            cached_data = [v for v in cached_data if v.get('slang_comment_count', 0) > 0]
            
        # Check for priority video
        if last_video_id:
            priority_list = [v for v in cached_data if v.get('video_id') == last_video_id]
            if priority_list:
                priority_video = priority_list[0]
                cached_data = [v for v in cached_data if v.get('video_id') != last_video_id]

        print(f"✅ Returning {len(cached_data) + (1 if priority_video else 0)} videos from SQLite (cached + priority)")
        random.shuffle(cached_data) 
        final_videos.extend(cached_data)
        
    # 3. If cache missed, attempt to fetch new data with retries
    else:
        MAX_RETRIES = 3
        shorts_data = []

        for attempt in range(MAX_RETRIES):
            try:
                print(f"🔄 Fetching fresh data from YouTube API for topics: {config.topics} (Attempt {attempt + 1}/{MAX_RETRIES})")
                shorts_data = fetcher.fetch_shorts(
                    topics=config.topics,
                    shorts_per_topic=shorts_per_topic, 
                    comments_per_short=config.comments_per_short
                )
                if shorts_data:
                    break
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    print(f"⚠️ Fetch attempt {attempt + 1} failed: {str(e)[:50]}... Retrying in 2 seconds.")
                    time.sleep(2) 
                else:
                    print(f"❌ Final fetch attempt failed after {MAX_RETRIES} retries. Error: {str(e)}")
                    raise HTTPException(status_code=504, detail=f"YouTube API Request Timeout/Failure: {str(e)}")


        # 4. Save cache & process data
        if shorts_data:
            db.cache_videos(
                videos=shorts_data,
                topics=config.topics,
                custom_slang=custom_slang,
                shorts_per_topic=shorts_per_topic, 
                comments_per_short=config.comments_per_short,
                cache_hours=24
            )
            print(f"💾 Cached {len(shorts_data)} videos to SQLite database")
            
            # Filter the newly fetched data before returning
            if slang_only:
                shorts_data = [v for v in shorts_data if v.get('slang_comment_count', 0) > 0]
            
            random.shuffle(shorts_data) 
            final_videos.extend(shorts_data)
            
            # Handle priority video in freshly fetched data
            if last_video_id and not priority_video:
                priority_list = [v for v in shorts_data if v.get('video_id') == last_video_id]
                if priority_list:
                    priority_video = priority_list[0]
                    final_videos = [v for v in final_videos if v.get('video_id') != last_video_id]


    # 5. Prepend the priority video (if found)
    if priority_video:
        final_videos.insert(0, priority_video)

    return final_videos


# ============================================================================
# 2. INITIALIZATION AND SETUP
# ============================================================================

# Check Groq availability
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


# ============================================================================
# 4. API ENDPOINTS
# ============================================================================

@app.get("/")
def home():
    return {
        "message": "Backend running with auto slang discovery and SQLite cache!",
        "slang_terms_loaded": len(slang_discovery.get_all_slang_terms()),
    }

# --- CACHE MANAGEMENT ENDPOINTS ---

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
        import sqlite3
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        # Get counts
        cursor.execute("SELECT COUNT(*) FROM videos")
        video_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM comments")
        comment_count = cursor.fetchone()[0]
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


# --- VIDEO FETCHING ENDPOINTS ---

@app.get("/api/videos")
def get_videos_db_get(
    topics: List[str] = ["gaming", "food review", "funny moments", "dance", "pets"],
    shorts_per_topic: int = 15, 
    comments_per_short: int = 30,
    slang_only: bool = False, # <-- FILTER PARAMETER
    last_video_id: Optional[str] = None
):
    """Fetches videos using Query Parameters (GET). Checks database cache first."""
    config = VideoConfig(
        topics=topics, 
        shorts_per_topic=shorts_per_topic, 
        comments_per_short=comments_per_short
    )
    return fetch_and_cache_videos(config, slang_only=slang_only, last_video_id=last_video_id)

@app.post("/api/videos")
def get_videos_db_post(config: VideoConfig, slang_only: bool = True, last_video_id: Optional[str] = None):
    """
    Fetches videos using a JSON Request Body (POST). Checks database cache first.
    Note: slang_only/last_video_id must be passed as query parameters if used with POST.
    """
    return fetch_and_cache_videos(config, slang_only=slang_only, last_video_id=last_video_id)


# --- SLANG DATABASE ENDPOINTS ---

@app.post("/api/discover-slang")
def manual_discovery(request: DiscoverRequest):
    """
    Manually triggers the full two-stage slang discovery flow:
    1. Fetches fresh comments from YouTube (Stage 0).
    2. Runs local frequency checks to find candidates (Stage 1 - internal).
    3. Uses Groq AI to verify and enrich candidates (Stage 2 - internal).
    """
    topics = request.topics
    print(f"\n🔍 Manual discovery started for topics: {topics}")
    
    # Ensure fetcher has current approved slang to detect new candidates accurately
    current_slang = slang_discovery.get_all_slang_terms() 
    fetcher.slang_terms = current_slang
    
    # 1. Fetch videos to get fresh comments (Aggressive parameters)
    shorts_data = fetcher.fetch_shorts(
        topics=topics,
        shorts_per_topic=40, # Maximize videos searched
        comments_per_short=80 # Maximize comments per video
    )
    
    # 2. Collect ALL comments for the discovery process
    all_comments = []
    for short in shorts_data:
        comments_with_slang = short.get('comments_with_slang', [])
        all_comments.extend(comments_with_slang)
    
    print(f"💬 Analyzing {len(all_comments)} comments for new candidates...")
    
    if len(all_comments) < 20:
        raise HTTPException(
            status_code=400, 
            detail="Not enough comments collected. Try different topics."
        )
        
    # 3. STAGE 1 & 2: Local Filter, AI Verification, and Save
    # We call the local filter here:
    candidates_with_context = extract_slang_candidates_with_context(all_comments)

    if not candidates_with_context:
        return {
            "message": "Discovery complete.",
            "discovered": 0,
            "total_slang_terms_now": len(slang_discovery.get_all_slang_terms()),
            "new_terms": [],
        }

    # Pass the filtered list to the AI verification step
    new_slang = slang_discovery.verify_and_enrich_slang(candidates_with_context)
    
    # Update fetcher again in case new slang was discovered and saved
    fetcher.slang_terms = slang_discovery.get_all_slang_terms()

    return {
        "message": "Discovery complete.",
        "discovered": len(new_slang),
        "total_slang_terms_now": len(fetcher.slang_terms),
        "new_terms": [
            {
                "term": s['term'],
                "definition": s['definition'],
                "category": s['category']
            } for s in new_slang
        ]
    }


@app.get("/api/slang")
def get_all_slang():
    """Get all known slang terms with definitions"""
    slang_db = slang_discovery.slang_database
    from collections import Counter # local import for category calculation
    
    categories = [info.get('category', 'unknown') for info in slang_db.values()]
    
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
        ],
        "slang_by_category": dict(Counter(categories))
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


# --- AI EVALUATION ENDPOINTS ---

@app.post("/api/evaluate", response_model=EvaluateResponse)
def evaluate_comment(request: EvaluateRequest):
    """Evaluate a user's comment on a video."""
    try:
        evaluation = groq_evaluator.evaluate_comment(
            video_title=request.videoTitle,
            video_description=request.videoDescription,
            user_comment=request.userComment,
            target_language=request.targetLanguage,
            video_like_count=request.videoLikeCount,
            available_slang=request.availableSlang,
            forbidden_slang=request.forbiddenSlang
        )
        return evaluation
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation error: {str(e)}")

@app.post("/api/respond", response_model=RespondResponse)
def generate_ai_response(request: RespondRequest):
    """Generate multiple Gen Z style AI responses to user's comment."""
    try:
        responses = groq_evaluator.generate_multiple_responses(
            user_comment=request.userComment,
            score=request.score,
            mistakes=request.mistakes,
            correction=request.correction,
            video_title=request.videoTitle,
            target_language=request.targetLanguage,
            available_slang=request.availableSlang,
            forbidden_slang=request.forbiddenSlang
        )
        return {"responses": responses}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Response generation error: {str(e)}")

@app.post("/api/explain-comment", response_model=ExplainCommentResponse)
def explain_comment(request: ExplainCommentRequest):
    """Explain a YouTube comment by translating it to simpler language and breaking down each slang term."""
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

@app.post("/api/translate-video", response_model=TranslateVideoResponse)
def translate_video(request: TranslateVideoRequest):
    """
    Translate a YouTube video's transcript to the target language and generate TTS audio.

    Flow:
    1. Fetch transcript using YouTube Transcript API
    2. Translate full transcript to target language using Groq LLM
    3. Generate TTS audio using Groq's PlayAI model
    4. Return transcript, translation, and audio
    """
    try:
        # Step 1: Fetch transcript from YouTube
        print(f"Fetching transcript for video: {request.video_id}")
        transcript_data = None

        # Create instance of the API (required for v1.2.3+)
        ytt_api = YouTubeTranscriptApi()

        # Try multiple methods to fetch transcripts (especially for YouTube Shorts)
        try:
            # Method 1: Try fetch() with default English settings (includes auto-generated)
            transcript_result = ytt_api.fetch(request.video_id, languages=['en', 'en-US', 'en-GB'])
            transcript_data = transcript_result.to_raw_data()
            print(f"✓ Transcript fetched: {len(transcript_data)} segments (is_generated: {transcript_result.is_generated})")
        except Exception as e1:
            print(f"Default transcript fetch failed: {str(e1)[:150]}")

            # Method 2: List all available transcripts and try manual + auto-generated explicitly
            try:
                transcript_list = ytt_api.list(request.video_id)
                print(f"Available transcripts: {[t.language_code for t in transcript_list]}")

                # Try manually created transcripts first
                try:
                    transcript = transcript_list.find_manually_created_transcript(['en', 'en-US', 'en-GB'])
                    transcript_result = transcript.fetch()
                    transcript_data = transcript_result.to_raw_data()
                    print(f"✓ Manual transcript found: {transcript.language_code}")
                except Exception as e2:
                    print(f"No manual transcript found: {str(e2)[:150]}")

                    # Try auto-generated transcripts (common for YouTube Shorts)
                    try:
                        transcript = transcript_list.find_generated_transcript(['en', 'en-US', 'en-GB', 'a.en'])
                        transcript_result = transcript.fetch()
                        transcript_data = transcript_result.to_raw_data()
                        print(f"✓ Auto-generated transcript found: {transcript.language_code}")
                    except Exception as e3:
                        print(f"No auto-generated transcript found: {str(e3)[:150]}")
            except Exception as e4:
                print(f"Failed to list transcripts: {str(e4)[:150]}")

        # If all methods failed, raise an error
        if not transcript_data:
            raise HTTPException(
                status_code=404,
                detail=f"No transcript available for video {request.video_id}. The video may not have captions or they may be disabled."
            )

        # Convert transcript to our model format
        transcript_segments = [
            TranscriptSegment(
                text=segment['text'],
                start=segment['start'],
                duration=segment['duration']
            )
            for segment in transcript_data
        ]

        # Step 2: Combine transcript into full text
        full_transcript = " ".join([seg.text for seg in transcript_segments])
        print(f"Transcript fetched: {len(full_transcript)} characters")

        # Step 3: Translate using Groq LLM
        print(f"Translating to {request.target_language}...")
        translation_prompt = f"""Translate the following English text to {request.target_language}.
Keep the translation natural and conversational, as this is from a YouTube video.

Text to translate:
{full_transcript}

Provide ONLY the translation, no explanations or additional text."""

        translation_response = groq_evaluator.client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": translation_prompt
            }],
            model=groq_evaluator.model,
            temperature=0.5,  # Lower temp for more accurate translation
            max_tokens=2000
        )

        translated_text = translation_response.choices[0].message.content.strip()
        print(f"Translation complete: {len(translated_text)} characters")

        # Step 4: Generate TTS audio
        print("Generating TTS audio...")
        audio_bytes = groq_evaluator.text_to_speech(
            text=translated_text,
            voice="Atlas-PlayAI",  # Default voice
            audio_format="mp3"
        )

        # Convert audio to base64 for transmission
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        print(f"TTS generation complete: {len(audio_bytes)} bytes")

        return TranslateVideoResponse(
            video_id=request.video_id,
            target_language=request.target_language,
            original_transcript=transcript_segments,
            translated_text=translated_text,
            audio_base64=audio_base64,
            audio_format="mp3"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in translate_video: {e}")
        raise HTTPException(status_code=500, detail=f"Translation error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚀 Starting Slang Learning Backend")
    print("="*60)
    print(f"📚 Loaded {len(slang_discovery.get_all_slang_terms())} slang terms")
    print("="*60 + "\n")
    uvicorn.run(app, host="127.0.0.1", port=3001, reload=True)

@app.post("/api/train-cache")
def train_cache():
    """
    NEW: Triggers the AI discovery flow using comments from all videos currently in the cache.
    This trains the AI on videos that the user is currently seeing, regardless of initial slang count.
    """
    print("\n🧠 Training started using all currently cached comments.")
    
    # 1. Collect ALL videos from the DB (using default cache parameters for a wide pull)
    # We use aggressive shorts/comments to ensure we retrieve max data points from cache.
    config_params = {
        "topics": ["gaming", "food review", "funny moments", "dance", "pets"],
        "shorts_per_topic": 15, # Try to pull deep cache
        "comments_per_short": 30
    }
    
    # Using a fake/expired cache entry lookup to force retrieval of all known data points
    cached_videos = db.get_cached_videos(
        topics=config_params['topics'],
        custom_slang=[],
        shorts_per_topic=config_params['shorts_per_topic'],
        comments_per_short=config_params['comments_per_short']
    )
    
    if not cached_videos:
        return {"message": "Cache is empty. Please refresh the video feed first."}

    # 2. Collect ALL comments for the discovery process
    all_comments = []
    for short in cached_videos:
        all_comments.extend(short.get('comments_with_slang', []))
    
    # Check if we have enough comments, otherwise the function won't be able to run
    if len(all_comments) < 20:
        return {"message": f"Collected only {len(all_comments)} comments from cache. Need 20+ to run AI verification."}
        
    print(f"💬 Collected {len(all_comments)} comments from cache for training.")

    # 3. STAGE 1 & 2: Local Filter, AI Verification, and Save
    # This automatically calls extract_slang_candidates_with_context internally
    new_slang = slang_discovery.process_discovery_flow(all_comments)
    
    # Update fetcher with newly discovered slang
    fetcher.slang_terms = slang_discovery.get_all_slang_terms()

    return {
        "message": "Cache training complete.",
        "discovered": len(new_slang),
        "total_slang_terms_now": len(fetcher.slang_terms),
        "new_terms": [
            {
                "term": s['term'],
                "definition": s['definition'],
                "category": s['category']
            } for s in new_slang
        ]
    }