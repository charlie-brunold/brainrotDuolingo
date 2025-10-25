# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from youtube_fetcher import YouTubeShortsSlangFetcher
from dotenv import load_dotenv
import os
from typing import List

# Load API key
load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")
if not API_KEY:
    raise ValueError("YOUTUBE_API_KEY missing in .env")

# Initialize FastAPI and fetcher
app = FastAPI()
fetcher = YouTubeShortsSlangFetcher(API_KEY)

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
