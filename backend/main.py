# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from youtube_fetcher import YouTubeShortsSlangFetcher
from groq_evaluator import GroqCommentEvaluator
from dotenv import load_dotenv
import os
from typing import List

# Load API keys
load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not YOUTUBE_API_KEY:
    raise ValueError("YOUTUBE_API_KEY missing in .env")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY missing in .env")

# Initialize FastAPI and services
app = FastAPI()
fetcher = YouTubeShortsSlangFetcher(YOUTUBE_API_KEY)
groq_evaluator = GroqCommentEvaluator(GROQ_API_KEY)

# Allow frontend to call
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:3000"] for security
    allow_methods=["*"],
    allow_headers=["*"]
)

cached_shorts = []

@app.get("/")
def home():
    return {"message": "Backend is running!"}


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

# main.py - inside refresh_videos (around line 36)
@app.post("/api/refresh")
def refresh_videos(topics: List[str] = ["gaming", "food review", "funny moments", "dance", "pets"]):
    global cached_shorts
    # Pass topics to the fetcher
    shorts_data = fetcher.fetch_shorts(topics)
    cached_shorts = shorts_data
    return shorts_data


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
    try:
        evaluation = groq_evaluator.evaluate_comment(
            video_title=request.videoTitle,
            video_description=request.videoDescription,
            user_comment=request.userComment,
            target_language=request.targetLanguage,
            video_view_count=request.videoViewCount,
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

    Returns:
        - responses: List of 2-4 AI responses, each with:
            - aiComment: TikTok-style roast-with-love feedback
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
