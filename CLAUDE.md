# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**LingoScroll/Brainrot Duolingo** - A language learning app disguised as TikTok. Users scroll through real YouTube Shorts, comment in any language, and receive instant AI feedback formatted as social validation (likes/comments). Learning feels like social media, not homework.

**Status**: Cal Hacks hackathon project. Core MVP complete with functional vertical scroll UI, YouTube API integration, and Groq AI comment evaluation.

## Commands

### Development

**Frontend** (React):
```bash
npm start          # Start React development server (port 3000)
npm run build      # Production build
npm test           # Run tests with Jest/React Testing Library
```

**Backend** (FastAPI):
```bash
# First time setup
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start backend server (port 3001)
cd backend
uvicorn main:app --reload --port 3001
# OR run from project root:
# uvicorn backend.main:app --reload --port 3001
```

**IMPORTANT**: For the app to work, you MUST:
1. Have both GROQ_API_KEY and YOUTUBE_API_KEY in your `.env` file (at project root)
2. Run the backend server on port 3001
3. Run `npm start` (frontend on port 3000)

### Python Scripts (Data Fetching & Testing)
```bash
# YouTube Shorts fetching with slang detection (requires YOUTUBE_API_KEY in .env)
python src/fetching.py

# Groq API testing (requires GROQ_API_KEY in .env)
python groq/test_groq.py
```

## Architecture

### Frontend-Backend Split

**Frontend** (React app in `/src`):
- Create React App setup with React 19.2.0
- Main component: `BrainrotTikTok.jsx` - Full TikTok-style vertical scroll UI
- **Vertical scrolling** implemented with:
  - Mouse wheel navigation
  - Touch swipe support (mobile)
  - ChevronUp/ChevronDown buttons
- **TikTok-style UI features**:
  - Embedded YouTube iframes for each Short
  - Right sidebar with like/comment/share/bookmark icons
  - Comments overlay with slang practice prompts
  - Real-time slang detection and feedback system
  - Mock AI responses for user comments
- Fetches video data from backend `/api/videos` endpoint
- Uses Tailwind CSS for styling (configured in `tailwind.config.js`)
- Static slang terms dictionary embedded in `BrainrotTikTok.jsx`

**Backend** (Python/FastAPI in `/backend`):
- FastAPI server with CORS enabled
- Single production endpoint:
  - `GET /api/videos`: Fetches YouTube Shorts with slang-enriched comments
    - Uses `YouTubeShortsSlangFetcher` class
    - Searches by topics: gaming, food review, funny moments, dance, pets
    - Filters for videos under 60 seconds
    - Fetches comments and detects slang using word-boundary regex
    - Returns enriched data with:
      - Video metadata (title, channel, thumbnail, URL, like_count, comment_count)
      - `comments_with_slang`: Comments containing slang terms with `detected_slang` array
      - `unique_slang_terms`: Deduplicated list of all slang in video comments
      - `slang_comment_count`: Number of comments containing slang
- Caches fetched shorts in memory to reduce API calls
- `POST /api/refresh`: Manually refresh video cache with new topics

**YouTube Integration** (`backend/youtube_fetcher.py`):
- `YouTubeShortsSlangFetcher` class handles all YouTube API interactions
- **Slang detection**: Matches 40+ terms (fr, ngl, bussin, sigma, rizz, etc.) using `\b` word boundaries
- **English filtering**: Only returns comments with ASCII characters
- **Multi-stage fetch**:
  1. Search for Shorts by topic
  2. Get detailed video statistics
  3. Fetch comments (up to 50 per video)
  4. Filter comments for slang
  5. Enrich video object with slang data

**Data Pipeline** (Python scripts):
- `src/fetching.py`: Standalone YouTube Shorts fetcher (alternate implementation)
- `groq/test_groq.py`: Groq API testing scripts (for future AI evaluation integration)

### Key Technical Decisions

**Video Context for AI Evaluation**:
- MVP: Send video title + description to Groq (always available from YouTube API)
- Future: Include captions/transcript for better accuracy (requires extra API call)

**AI Feedback Format** (Groq prompt design):
- **Evaluation**: Score 0-100 based on grammar (50%), relevance (30%), vocabulary (20%)
- **Social Validation**: Tiered like count proportional to score (not video likes)
- **AI Response**: Roast-with-love personality with Gen Z energy
  - 1-2 sentences max, TikTok-style with emojis
  - Playfully roasts mistakes while teaching
  - Examples:
    - "Bro really said 'I eated' 😭 it's 'I ate' but A+ for confidence lmao"
    - "Nah the grammar was lowkey fire but 'estaba' not 'era' bestie 💀"
    - "SHEEEESH that was actually clean ngl 🔥 keep it up fam"

**Component Structure**:
- `App.js`: Main component with video display, comment input, two-stage evaluation flow
  - Uses `extractVideoId()` to handle both `/watch?v=` and `/shorts/` URLs
  - **Two-stage flow**:
    1. `handleEvaluate()` calls `/api/evaluate` for scoring
    2. Auto-calls `/api/respond` for AI response if score > 0
  - **TikTok-style UI**: Comment thread showing user comment + likes + AI coach response
  - Score badges with color coding (green 75+, yellow 50+, red <50)
  - Collapsible detailed feedback (correction, mistakes, good parts)
- Static data from `youtube_shorts_slang_data.json` for development

**State Management**:
- React `useState` hooks (no Redux/Context needed for MVP)
- Ephemeral session state - no persistence or user accounts

**YouTube API Integration**:
- Search endpoint with filters: `videoDuration=short`, `relevanceLanguage=[target]`
- Free tier: 10k units/day quota (manage rate limits)
- Python `YouTubeShortsSlangFetcher` class in `src/fetching.py`

**Groq API**:
- Model: `llama-3.3-70b-versatile` (updated from deprecated llama-3.1)
- Target: <1s response time for instant feedback
- API key in `.env` (see `.env.example`)

## Environment Variables

Required in `.env` file (see `.env.example`):
- `GROQ_API_KEY`: Groq API key for AI evaluation
- YouTube API key (not yet configured) for video fetching

**IMPORTANT**: `.env` is gitignored. Never commit API keys.

## Implementation Status

**✅ Completed**:
1. ✅ Backend API server with Groq integration (`/api/evaluate` + `/api/respond`)
2. ✅ Frontend-backend connection with two-stage API flow
3. ✅ TikTok-style comment thread UI with likes and AI responses
4. ✅ Tiered social validation system (score → likes mapping)
5. ✅ Roast-with-love AI personality

**🚧 MVP Enhancements Needed**:
1. **Vertical scroll UI**: Currently uses prev/next buttons (not true TikTok scroll)
2. **Framer Motion animations**: Add smooth transitions between videos
3. **Multi-language support**: Currently hardcoded to English (line 42 in App.js)
4. **Language selection UI**: Dropdown for target language
5. **Better video filtering**: Integrate YouTube API calls for dynamic content

## Development Notes

- **No build errors expected**: Standard CRA setup, React 19.2.0 compatible
- **Routing**: Currently a single-page app; no React Router needed for MVP
- **Testing**: `@testing-library/react` and Jest configured but tests not written
- **Styling**: Inline styles in components; Tailwind CSS planned but not installed
- **Backend dependencies**: Tracked in `backend/requirements.txt` (flask, flask-cors, groq, python-dotenv)
- **Groq API Performance**: Sub-second response times (<1s) for instant feedback
- **Error Handling**: Backend validates JSON responses and strips markdown code blocks if present
