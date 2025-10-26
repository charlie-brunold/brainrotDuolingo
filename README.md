# Brainrot Duolingo

Learn any language by scrolling through YouTube Shorts and commenting like you're on TikTok. Watch authentic content, pick up on memes and cultural references, then practice by commenting in your target language. AI evaluates your comments instantly and gives you feedback disguised as social validation—likes, replies, and roasts that teach. Language learning that feels like scrolling, not studying.

## Setup

**Prerequisites**: Node.js, Python 3, and API keys for Groq and YouTube Data API v3

1. **Clone and install dependencies**
   ```bash
   git clone <repo-url>
   cd brainrotDuolingo
   npm install
   ```

2. **Set up environment variables**
   - Create a `.env` file in the project root
   - Add your API keys:
     ```
     GROQ_API_KEY=your_groq_api_key_here
     YOUTUBE_API_KEY=your_youtube_api_key_here
     ```

3. **Set up the backend**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Run the app**
   - **Terminal 1** (Backend):
     ```bash
     cd backend
     source venv/bin/activate
     uvicorn main:app --reload --port 3001
     ```
   - **Terminal 2** (Frontend):
     ```bash
     npm start
     ```

5. **Open** `http://localhost:3000` and start scrolling

## Tech Stack

- React frontend with TikTok-style vertical scroll
- FastAPI backend with YouTube Data API v3 integration
- Groq AI (llama-3.3-70b-versatile) for sub-1s comment evaluation
