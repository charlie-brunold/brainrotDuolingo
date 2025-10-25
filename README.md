# Brainrot Duolingo

Learn languages by scrolling TikTok-style videos and leaving comments.

## What is this?

You want to learn Spanish. You hate Duolingo. You love scrolling through short videos.

Brainrot Duolingo shows you real YouTube Shorts in your target language. You comment on them in that language. AI instantly tells you if your comment makes sense, gives you feedback disguised as "social validation" (likes, supportive comments), and you scroll to the next one.

It's language learning that feels like wasting time on social media.

## How it works

1. Watch a YouTube Short in Spanish (or whatever language)
2. Comment on it in Spanish
3. AI evaluates your comment based on the video context
4. You get instant feedback: hearts/likes for good comments, gentle corrections for mistakes
5. AI replies like other "users" would - encouraging you and helping you improve
6. Scroll to next video

## The trick

Traditional language apps feel like homework. This feels like scrolling Instagram. You're learning without realizing it because the feedback looks like social validation, not a teacher marking your quiz.

## Tech

- **YouTube Data API v3** - fetches real Shorts in the target language
- **Groq API** (llama-3.1-70b-versatile) - evaluates comments in <1 second
- **React/Next.js** - TikTok-style vertical feed
- **Tailwind + Framer Motion** - smooth animations

## Why this works

- Real content > synthetic exercises
- Instant feedback > delayed corrections
- Social validation > red X marks
- Scrolling > clicking "next lesson"
