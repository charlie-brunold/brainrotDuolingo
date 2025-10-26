import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from youtube_fetcher import YouTubeShortsSlangFetcher
from groq_evaluator import GroqCommentEvaluator
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
class VideoConfig(BaseModel):
    topics: List[str] = ["gaming", "food review", "funny moments", "dance", "pets"]
    shorts_per_topic: int = 15

# AI Evaluation Models (Abbreviated for brevity, assuming standard structure)
class EvaluateRequest(BaseModel):
    videoTitle: str
    videoDescription: str
    userComment: str
    targetLanguage: str
    videoLikeCount: int
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

class AIResponse(BaseModel):
    aiComment: str
    authorName: str
    likes: int

class RespondResponse(BaseModel):
    responses: List[AIResponse]

class ExplainCommentRequest(BaseModel):
    commentText: str
    videoTitle: str
    videoDescription: str
    detectedSlang: List[str] = []

class ExplainCommentResponse(BaseModel):
    translation: str
    context: str  # General context explanation

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

def fetch_and_cache_videos(config: VideoConfig, last_video_id: Optional[str] = None):
    """
    Unified function to check cache, fetch videos from YouTube, and save results to DB.
    """
    
    # Cache Busting logic
    shorts_per_topic_base = config.shorts_per_topic
    shorts_per_topic = shorts_per_topic_base + random.choice([0, 0, 1, 1, 2, 2])
    
    # 2. Check database cache (read operation)
    cached_data = db.get_cached_videos(
        topics=config.topics,
        custom_slang=[],  # No custom slang anymore
        shorts_per_topic=shorts_per_topic,
        comments_per_short=30  # Fixed value
    )
    
    final_videos = []
    priority_video = None
    
    # Handle cache hit
    if cached_data:
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
                    shorts_per_topic=shorts_per_topic  # ✅ Just 2 parameters!
                )
                if shorts_data:
                    break
            except Exception as e:
                error_message = str(e)
                if attempt < MAX_RETRIES - 1:
                    print(f"⚠️ Fetch attempt {attempt + 1} failed: {error_message[:50]}... Retrying in 2 seconds.")
                    time.sleep(2)
                else:
                    # On final failure, try to return ANY cached videos as fallback
                    print(f"❌ Final fetch attempt failed after {MAX_RETRIES} retries. Error: {error_message}")
                    print(f"🔍 Attempting to fall back to any available cached videos...")

                    fallback_videos = db.get_any_cached_videos(limit=20)
                    if fallback_videos:
                        print(f"✅ Found {len(fallback_videos)} fallback videos from cache (quota exhausted)")
                        random.shuffle(fallback_videos)
                        return fallback_videos
                    else:
                        raise HTTPException(
                            status_code=503,
                            detail=f"YouTube API quota exhausted (resets midnight PT). No cached videos available. Error: {error_message}"
                        )


        # 4. Save cache & process data
        if shorts_data:
            db.cache_videos(
                videos=shorts_data,
                topics=config.topics,
                custom_slang=[],  # No custom slang
                shorts_per_topic=shorts_per_topic,
                comments_per_short=30,  # Fixed value
                cache_hours=72  # Extended to 3 days to handle quota issues
            )
            print(f"💾 Cached {len(shorts_data)} videos to SQLite database")
            
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
db = VideoDatabase()

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
        "message": "Backend running!",
        "status": "ok"
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
    last_video_id: Optional[str] = None
):
    """Fetches videos using Query Parameters (GET). Checks database cache first."""
    config = VideoConfig(topics=topics, shorts_per_topic=shorts_per_topic)
    return fetch_and_cache_videos(config, last_video_id=last_video_id)

@app.post("/api/videos")
def get_videos_db_post(config: VideoConfig, last_video_id: Optional[str] = None):
    """
    Fetches videos using a JSON Request Body (POST). Checks database cache first.
    """
    return fetch_and_cache_videos(config, last_video_id=last_video_id)


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
            video_like_count=request.videoLikeCount
        )
        return evaluation
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation error: {str(e)}")

@app.post("/api/define-word")
def define_word(request: dict):
    """Get definition for any word using AI"""
    word = request.get('word', '')
    context = request.get('context', '')
    
    try:
        prompt = f"""Define the word "{word}" in the context of the comment for someone learning English. 
        
Context: {context}

Provide:
1. A simple, clear definition (1-2 sentences)
2. An example sentence using the word naturally

Format as JSON:
{{
  "word": "{word}",
  "definition": "...",
  "example": "..."
}}"""

        response = groq_evaluator.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=groq_evaluator.model,
            temperature=0.7,
            max_tokens=200
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        return {
            "word": word,
            "definition": "Definition not available",
            "example": ""
        }


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
            target_language=request.targetLanguage
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
    print("🚀 Starting Language Learning Backend")
    print("="*60)
    print(f"🌐 Server: http://127.0.0.1:3001")
    print("="*60 + "\n")
    uvicorn.run(app, host="127.0.0.1", port=3001, reload=True)