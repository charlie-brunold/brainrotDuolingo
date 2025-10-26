# Groq Comment Integration - Design Philosophy & Implementation Guide

## Executive Summary

This document outlines the design philosophy for integrating Groq AI into a language learning application that gamifies feedback through social validation. The system evaluates user comments on videos and provides instant, engaging feedback formatted as TikTok-style social interactions (likes, AI responses).

**Core Innovation**: Language learning disguised as social media engagement. Users don't feel like they're studying—they feel like they're getting social validation.

---

## Architecture Overview

### Two-Stage API Design

The system uses **two separate API endpoints** rather than a single monolithic call. This separation provides:

1. **Modularity**: Each endpoint has a single responsibility
2. **Flexibility**: Frontend can call them independently or sequentially
3. **Performance visibility**: Can measure and optimize each stage separately
4. **Error isolation**: Failure in one stage doesn't block the other

```
User submits comment
    ↓
[Stage 1] POST /api/evaluate
    → Scores comment (0-100)
    → Returns tiered/percentage-based likes
    → Provides detailed feedback
    ↓
[Stage 2] POST /api/respond
    → Generates AI personality response
    → Returns roast-with-love comment
    → Includes AI author name + random likes
```

---

## Stage 1: Comment Evaluation (`/api/evaluate`)

### Design Philosophy

**Goal**: Provide objective, detailed scoring that feels like social validation rather than a teacher's grade.

**Scoring Weights** (0-100 scale):
- **Grammar/Language Accuracy**: 50% weight
  - Most important for language learning
  - Clear, measurable improvement path
- **Relevance to Video**: 30% weight
  - Ensures comprehension, not just translation
  - Prevents off-topic responses
- **Vocabulary/Naturalness**: 20% weight
  - Rewards idiomatic usage
  - Encourages authentic expression

### Prompt Engineering Strategy

**Key Principles**:
1. **Explicit JSON formatting**: LLMs sometimes wrap JSON in markdown. The prompt explicitly demands raw JSON with no formatting.
2. **Context-rich input**: Include video title + description (not just comment in isolation)
3. **Structured output**: Define exact JSON schema in the prompt
4. **Weighted criteria**: Explain the 50/30/20 split to the model
5. **Balanced feedback**: Request both `mistakes` AND `goodParts` arrays

**Prompt Structure**:
```
You are a language learning evaluator. Analyze this user's comment.

[Video Context]
Video Title: {title}
Video Description: {description}

[User Input]
Comment: {userComment}
Target Language: {targetLanguage}

[Evaluation Criteria]
Score 0-100 based on:
1. Grammar/accuracy (50% weight)
2. Relevance to video (30% weight)
3. Vocabulary/naturalness (20% weight)

[Output Format]
Return ONLY valid JSON (no markdown, no code blocks):
{
  "score": <0-100>,
  "grammarScore": <0-100>,
  "contextScore": <0-100>,
  "naturalnessScore": <0-100>,
  "correction": "<corrected version or 'No correction needed'>",
  "mistakes": ["<mistake 1>", ...],
  "goodParts": ["<positive observation 1>", ...]
}
```

**Backend Processing**:
- Strip markdown code blocks if present (```json wrapper)
- Validate JSON parsing
- Calculate social validation (likes) from score
- Return enriched response to frontend

---

## Like Calculation System

### Original Tiered System (Current Implementation)

**Philosophy**: Fixed tiers that feel like virality levels

```python
def calculate_tiered_likes(score):
    if score >= 90:    return random.randint(10000, 50000)  # Viral
    elif score >= 75:  return random.randint(1000, 9999)    # Popular
    elif score >= 60:  return random.randint(500, 999)      # Solid
    elif score >= 40:  return random.randint(100, 499)      # Decent
    else:              return random.randint(1, 99)         # Needs work
```

**Pros**: Simple, consistent across videos
**Cons**: Doesn't reflect actual video popularity

---

### Recommended: View-Based Percentage System

**Philosophy**: Likes should feel proportional to video reach. A viral comment on a viral video gets massive likes.

**Algorithm Design**:

```python
def calculate_view_based_likes(score, video_view_count):
    """
    Calculate likes as percentage of video views based on score.

    Score Tiers:
    - 90-100: Super viral (15-20% of views)
    - 80-89:  Viral (8-15% of views)
    - 70-79:  Popular (4-8% of views)
    - 60-69:  Above average (2-4% of views)
    - 50-59:  Average (0.5-2% of views)
    - 40-49:  Below average (0.1-0.5% of views)
    - 0-39:   Poor (0.01-0.1% of views)

    Args:
        score: 0-100 evaluation score
        video_view_count: number of views on the video

    Returns:
        int: calculated like count
    """
    import random

    # Define percentage ranges for each tier
    if score >= 90:
        percentage = random.uniform(0.15, 0.20)      # 15-20%
    elif score >= 80:
        percentage = random.uniform(0.08, 0.15)      # 8-15%
    elif score >= 70:
        percentage = random.uniform(0.04, 0.08)      # 4-8%
    elif score >= 60:
        percentage = random.uniform(0.02, 0.04)      # 2-4%
    elif score >= 50:
        percentage = random.uniform(0.005, 0.02)     # 0.5-2%
    elif score >= 40:
        percentage = random.uniform(0.001, 0.005)    # 0.1-0.5%
    else:
        percentage = random.uniform(0.0001, 0.001)   # 0.01-0.1%

    # Calculate likes and ensure minimum of 1
    likes = int(video_view_count * percentage)
    return max(1, likes)
```

**Example Calculations**:

| Score | Video Views | Percentage Range | Like Range |
|-------|-------------|------------------|------------|
| 95    | 500M        | 15-20%           | 75M-100M   |
| 95    | 10K         | 15-20%           | 1.5K-2K    |
| 75    | 500M        | 4-8%             | 20M-40M    |
| 75    | 10K         | 4-8%             | 400-800    |
| 45    | 500M        | 0.1-0.5%         | 500K-2.5M  |
| 45    | 10K         | 0.1-0.5%         | 10-50      |

**Why This Works**:
- ✅ Feels realistic (proportional to video popularity)
- ✅ Still gamified (dramatic difference between tiers)
- ✅ Motivating (even low scores get *some* validation on viral videos)
- ✅ Contextual (same quality comment performs differently on different videos)

**Implementation Notes**:
- Frontend must send `videoViewCount` in the request payload
- Backend receives: `videoTitle`, `videoDescription`, `userComment`, `targetLanguage`, **`videoViewCount`**
- Calculate likes AFTER receiving score from Groq
- Return `likes` field alongside evaluation data

---

## Stage 2: AI Response (`/api/respond`)

### Design Philosophy

**Goal**: Make feedback engaging, memorable, and funny—not dry or academic.

**Personality**: "Roast-with-Love Comedian"
- **Roasts mistakes** playfully (never mean-spirited)
- **Gives actionable tips** (specific, not generic)
- **Uses Gen Z language** (emojis, slang, internet speak)
- **Keeps it SHORT** (1-2 sentences max, TikTok attention span)

### Prompt Engineering Strategy

**Key Principles**:
1. **Tone calibration**: Higher scores → more encouraging, lower scores → more roasting
2. **Brevity enforcement**: "1-2 sentences MAX" in the prompt
3. **Style examples**: Show the model what you want (3-4 example outputs)
4. **Temperature**: Higher temp (0.9) for creative/funny responses
5. **No JSON needed**: Plain text output, easier for LLM

**Prompt Structure**:
```
You are a roasting language coach with Gen Z energy and TikTok vibes.

[Context]
The user commented on: "{videoTitle}"
Their comment: "{userComment}"
Their score: {score}/100
Target language: {targetLanguage}

[Mistakes] (if any)
{mistakes list}
{correction}

[Task]
Write a SHORT (1-2 sentences max) TikTok-style comment that:
1. Playfully roasts their mistakes (if score < 85)
2. Gives a quick, actionable learning tip
3. Uses emojis, slang, Gen Z speak
4. Keeps it supportive but hilarious

[Style Examples]
- "Bro really said 'I eated' 😭 it's 'I ate' but A+ for confidence lmao"
- "Nah the grammar was lowkey fire but 'estaba' not 'era' bestie 💀"
- "Not you using present tense for past events 😩 still understood you tho fr"
- "SHEEEESH that was actually clean ngl 🔥 keep it up fam"

If they scored 85+, be MORE encouraging.
If they scored <60, roast HARDER but still supportive.

Respond with ONLY the comment text, nothing else.
```

**Backend Processing**:
- No JSON parsing needed (plain text response)
- Generate random AI author name from predefined list
  - Examples: "LinguaLegend", "GrammarGoddess", "SyntaxSavage", "VocabVibes"
- Generate random like count for AI comment (10-500 range)
  - This is separate from user's likes (represents engagement on the AI's comment)

---

## Frontend Integration

### Two-Stage Flow

```javascript
const handleEvaluate = async () => {
  setLoading(true);

  // Stage 1: Evaluate comment
  const evalResponse = await fetch('/api/evaluate', {
    method: 'POST',
    body: JSON.stringify({
      videoTitle,
      videoDescription,
      userComment,
      targetLanguage,
      videoViewCount  // NEW: for percentage-based likes
    })
  });

  const evaluation = await evalResponse.json();
  setEvaluation(evaluation);  // Shows user's score + likes

  // Stage 2: Get AI response (only if score > 0)
  if (evaluation.score > 0) {
    const aiResponse = await fetch('/api/respond', {
      method: 'POST',
      body: JSON.stringify({
        userComment,
        score: evaluation.score,
        mistakes: evaluation.mistakes,
        correction: evaluation.correction,
        videoTitle,
        targetLanguage
      })
    });

    const aiData = await aiResponse.json();
    setAiResponse(aiData);  // Shows AI coach comment
  }

  setLoading(false);
};
```

### UI Design Philosophy

**TikTok-Style Comment Thread**:
- User's comment displayed first (primary position)
- Like count next to user comment (big, visible)
- Score badges with color coding:
  - Green (≥75): Good job!
  - Yellow (50-74): Room for improvement
  - Red (<50): Needs work
- Collapsible detailed feedback (correction, mistakes, good parts)
- AI response indented/styled differently (secondary position)
- AI has badge ("AI Coach") and random author name

**Visual Hierarchy**:
```
┌─────────────────────────────────────┐
│ 💬 You              ❤️ 2.4M likes  │  ← User comment (primary)
│ "Me encanta este video!"           │
│ Score: 85/100 🟢 Grammar:90 ...    │
│ [View Detailed Feedback ▼]         │
└─────────────────────────────────────┘
  ┌───────────────────────────────────┐
  │ 💬 GrammarGoddess [AI Coach]     │  ← AI response (secondary)
  │     ❤️ 234                        │
  │ "Yooo that was fire ngl 🔥       │
  │ just watch out for subjunctive!"  │
  └───────────────────────────────────┘
```

---

## Technical Implementation Guide

### Backend Requirements

**Language**: Any (Python/Flask, Node.js/Express, etc.)

**Dependencies**:
- Groq SDK (Python: `groq`, Node: `groq-sdk`)
- Web framework (Flask, Express, FastAPI, etc.)
- CORS support (for React frontend)
- Environment variable management

**Environment Variables**:
```bash
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxx
```

**Groq Configuration**:
```python
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Model: Use latest 70B parameter model
MODEL = "llama-3.3-70b-versatile"  # (as of Oct 2024)

# Stage 1 (Evaluation): Lower temp for consistency
response = client.chat.completions.create(
    messages=[...],
    model=MODEL,
    temperature=0.7,      # Balance between consistent and natural
    max_tokens=1000       # Enough for detailed JSON response
)

# Stage 2 (AI Response): Higher temp for creativity
response = client.chat.completions.create(
    messages=[...],
    model=MODEL,
    temperature=0.9,      # More creative/funny
    max_tokens=200        # Short response only
)
```

### Error Handling

**Common Issues**:

1. **JSON Parsing Failures** (Evaluation endpoint)
   - LLM sometimes wraps JSON in markdown (```json ... ```)
   - Solution: Strip code blocks before parsing
   ```python
   response_text = response.choices[0].message.content.strip()
   if response_text.startswith("```"):
       response_text = response_text.split("```")[1]
       if response_text.startswith("json"):
           response_text = response_text[4:]
       response_text = response_text.strip()
   data = json.loads(response_text)
   ```

2. **Model Deprecation**
   - Groq regularly updates models
   - Solution: Check deprecation notices, use latest 70B model
   - Current: `llama-3.3-70b-versatile`

3. **Rate Limiting**
   - Groq has rate limits on free tier
   - Solution: Implement retry logic, cache common evaluations

4. **API Key Issues**
   - Missing or invalid key
   - Solution: Check on app startup, fail fast with clear error

---

## Performance Considerations

**Target Response Time**: <1 second for instant feedback feel

**Optimization Strategies**:
1. **Parallel requests**: Frontend can fire both stages simultaneously if needed
2. **Streaming**: Groq supports streaming for progressive UI updates
3. **Caching**: Cache evaluations for identical comments (low priority for MVP)
4. **Model selection**: 70B models are slower but more accurate than 8B

**Actual Performance** (observed):
- Evaluation: ~500-800ms
- AI Response: ~300-600ms
- Total: ~1-1.5s for full flow

---

## Multi-Language Support

**Current**: Hardcoded to English in examples

**Scalability Strategy**:
1. Add language dropdown in frontend UI
2. Pass `targetLanguage` parameter to both endpoints
3. Groq models are multilingual—no prompt changes needed
4. Consider adding language-specific slang/idioms to AI personality

**Supported Languages** (via Groq Llama models):
- Spanish, French, German, Italian, Portuguese
- Chinese, Japanese, Korean
- Arabic, Hindi, and 20+ others

---

## Testing Strategy

### Manual Testing Script

Create test JSON files for quick validation:

**test_evaluation.json**:
```json
{
  "videoTitle": "How to make tacos",
  "videoDescription": "Learn authentic Mexican cooking",
  "userComment": "This is helpful, I love tacos!",
  "targetLanguage": "English",
  "videoViewCount": 1000000
}
```

**Test with curl**:
```bash
curl -X POST http://localhost:3001/api/evaluate \
  -H "Content-Type: application/json" \
  --data @test_evaluation.json
```

### Expected Outputs

**Good Comment** (score ~90):
```json
{
  "score": 92,
  "grammarScore": 100,
  "contextScore": 96,
  "naturalnessScore": 88,
  "likes": 180000,  // 15-20% of 1M views
  "correction": "No correction needed",
  "mistakes": [],
  "goodParts": ["Clear expression", "Relevant to video"]
}
```

**Bad Comment** (score ~45):
```json
{
  "score": 45,
  "grammarScore": 40,
  "contextScore": 60,
  "naturalnessScore": 50,
  "likes": 2000,  // 0.1-0.5% of 1M views
  "correction": "I ate tacos yesterday",
  "mistakes": ["Used 'eated' instead of 'ate'"],
  "goodParts": ["Attempted past tense"]
}
```

---

## Implementation Checklist

### Backend Setup
- [ ] Install Groq SDK
- [ ] Set up GROQ_API_KEY in environment
- [ ] Create `/api/evaluate` endpoint
- [ ] Create `/api/respond` endpoint
- [ ] Implement view-based percentage like calculation
- [ ] Add JSON parsing with markdown strip logic
- [ ] Enable CORS for frontend integration
- [ ] Test with curl/Postman

### Frontend Integration
- [ ] Add comment input UI
- [ ] Implement two-stage API call flow
- [ ] Show loading states
- [ ] Display user comment with likes
- [ ] Display score badges (color-coded)
- [ ] Add collapsible detailed feedback
- [ ] Display AI response with author name
- [ ] Add error handling
- [ ] Test full user flow

### Prompt for Claude Code

When asking another Claude Code instance to implement this, provide:

**Prompt Template**:
```
I need you to integrate Groq AI comment evaluation into my backend.

CONTEXT:
- This is a language learning app where users comment on videos
- We provide instant feedback formatted as social validation (likes + AI responses)
- Backend: [YOUR BACKEND TECH - e.g., "Python/Flask" or "Node.js/Express"]
- Groq API key is in environment variable: GROQ_API_KEY

REQUIREMENTS:

1. Create two separate API endpoints:

   a) POST /api/evaluate
      - Input: videoTitle, videoDescription, userComment, targetLanguage, videoViewCount
      - Call Groq with evaluation prompt (see design doc)
      - Calculate likes using VIEW-BASED PERCENTAGE system:
        * Score 90-100: 15-20% of video views
        * Score 80-89: 8-15% of video views
        * Score 70-79: 4-8% of video views
        * Score 60-69: 2-4% of video views
        * Score 50-59: 0.5-2% of video views
        * Score 40-49: 0.1-0.5% of video views
        * Score 0-39: 0.01-0.1% of video views
      - Return: score, likes, grammarScore, contextScore, naturalnessScore,
                correction, mistakes[], goodParts[]

   b) POST /api/respond
      - Input: userComment, score, mistakes[], correction, videoTitle, targetLanguage
      - Call Groq with roast-with-love personality prompt
      - Return: aiComment, authorName (random from list), likes (10-500)

2. Use Groq model: llama-3.3-70b-versatile
   - Evaluation: temperature=0.7, max_tokens=1000
   - AI Response: temperature=0.9, max_tokens=200

3. Handle JSON parsing errors (strip markdown code blocks)

4. Enable CORS for frontend at http://localhost:3000

REFER TO: /GROQ_INTEGRATION_DESIGN.md for full design philosophy

Please implement these endpoints following the design patterns in the document.
```

---

## Design Rationale Summary

| Decision | Rationale |
|----------|-----------|
| **Two-stage API** | Modularity, flexibility, performance visibility |
| **50/30/20 weighting** | Grammar most important, but context matters |
| **View-based percentages** | Feels realistic, contextual, still gamified |
| **Roast-with-love tone** | Engaging, memorable, reduces learning anxiety |
| **Short AI responses** | TikTok attention span, easy to read |
| **Color-coded scores** | Instant visual feedback, game-like |
| **Separate AI likes** | Simulates real social thread engagement |
| **No markdown in prompts** | Prevents JSON parsing issues |
| **Higher temp for AI** | More creative/funny responses |

---

## Future Enhancements

1. **Adaptive Difficulty**: Track user progress, adjust scoring rubric over time
2. **Streak System**: Reward consecutive high-scoring comments
3. **Leaderboards**: Compare likes/scores with other learners
4. **Voice Comments**: Evaluate pronunciation in addition to text
5. **Multi-turn Conversations**: AI responds to follow-up questions
6. **Personalized Coaching**: Tailor roasts/tips to user's weak areas
7. **A/B Testing**: Experiment with different AI personalities

---

## Conclusion

This design transforms language learning from tedious study into addictive social engagement. The key is making every interaction feel like winning at social media, not failing at school.

**Core Principle**: If it doesn't feel like TikTok, it's not working.

For implementation support, refer to the working reference implementation in `backend/server.py`.
