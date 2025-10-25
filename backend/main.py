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


# Request model for user configuration
class UserConfig(BaseModel):
    topics: List[str]
    custom_slang: List[str] = []
    shorts_per_topic: int = 10
    comments_per_short: int = 50

@app.post("/api/videos")
def get_videos(config: UserConfig):
    global cached_shorts
    # Use user's topics instead of default ones
    topics = config.topics if config.topics else ["gaming", "food review", "funny moments"]
    custom_slang = config.custom_slang if config.custom_slang else []
    
    try:
        # Try to fetch real videos with user's configuration
        shorts_data = fetcher.fetch_shorts(
            topics=topics,
            shorts_per_topic=config.shorts_per_topic,
            comments_per_short=config.comments_per_short,
            custom_slang=custom_slang
        )
        cached_shorts = shorts_data
        return shorts_data
    except Exception as e:
        print(f"Error fetching real videos: {e}")
        # Return mock data for testing
        return get_mock_videos(topics, custom_slang)

def get_mock_videos(topics, custom_slang):
    """Generate mock video data for testing when YouTube API is not available"""
    mock_videos = []
    slang_terms = ['fr', 'ngl', 'tbh', 'bussin', 'sigma', 'lit', 'cap', 'nocap', 'vibe', 'slay', 'goat', 'based', 'yeet', 'slaps', 'valid', 'mood']
    if custom_slang:
        slang_terms.extend(custom_slang)
    
    for i, topic in enumerate(topics[:3]):  # Limit to 3 topics for mock
        for j in range(2):  # 2 videos per topic
            video_id = f"mock_{topic}_{j}"
            mock_videos.append({
                'video_id': video_id,
                'title': f"Amazing {topic} video #{j+1}",
                'description': f"This is a great {topic} short that everyone loves!",
                'channel': f"{topic.capitalize()}Channel",
                'thumbnail': f"https://via.placeholder.com/480x360/ff6b6b/ffffff?text={topic.replace(' ', '+')}",
                'duration_seconds': 30 + (j * 15),
                'view_count': 100000 + (i * 50000) + (j * 25000),
                'like_count': 5000 + (i * 2000) + (j * 1000),
                'comment_count': 200 + (i * 50) + (j * 25),
                'url': f"https://www.youtube.com/shorts/{video_id}",
                'comments_with_slang': [
                    {
                        'comment_id': f"comment_{i}_{j}_1",
                        'text': f"This {topic} content is {slang_terms[i % len(slang_terms)]} fr!",
                        'author': f"User{i}{j}",
                        'like_count': 10 + (i * 5) + j,
                        'detected_slang': [slang_terms[i % len(slang_terms)]]
                    },
                    {
                        'comment_id': f"comment_{i}_{j}_2", 
                        'text': f"Bro this is {slang_terms[(i+1) % len(slang_terms)]} no cap",
                        'author': f"Viewer{i}{j}",
                        'like_count': 5 + (i * 3) + j,
                        'detected_slang': [slang_terms[(i+1) % len(slang_terms)]]
                    }
                ],
                'slang_comment_count': 2,
                'unique_slang_terms': [slang_terms[i % len(slang_terms)], slang_terms[(i+1) % len(slang_terms)]]
            })
    
    return mock_videos
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
