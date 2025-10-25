# Brainrot Duolingo

Learn how real people actually speak by scrolling through YouTube Shorts and commenting in your target language. If you're a non-native speaker struggling to understand slang like "bussin", "fr", or "ngl", this app gives you a safe space to see these terms used in context and practice using them yourself. AI evaluates your comments and gives you instant feedback disguised as social validation—so learning feels like scrolling TikTok, not doing homework.

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
