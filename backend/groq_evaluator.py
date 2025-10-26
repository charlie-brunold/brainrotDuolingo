# groq_evaluator.py - Friendly Version 😊

import os
import json
import random
from typing import Dict, List, Optional
from groq import Groq

class GroqCommentEvaluator:
    """
    Evaluates user comments with encouragement and positivity!
    Focuses on communication success rather than perfection.
    """

    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"

        # Mix of learning-focused and casual usernames
        self.ai_authors = [
            # Learning buddies
            "LinguaLegend",
            "GrammarGoddess",
            "VocabVibes",
            "WordWizard",
            "FluentFiend",
            
            # Casual viewers (more human-like)
            "sarah_learns",
            "mike_2024",
            "jenny_xo",
            "alex_codes",
            "random_viewer",
            "just_browsing",
            "foodie_fan",
            "casual_learner",
            
            # Mix of both
            "LanguageLover_23",
            "practicing_english",
            "learnwithme",
            "studying_vibes",
            
            # Very casual
            "user12345",
            "anon_user",
            "viewer_789"
        ]

    def evaluate_comment(
        self,
        video_title: str,
        video_description: str,
        user_comment: str,
        target_language: str,
        video_like_count: int
    ) -> Dict:
        """
        Evaluate a user's comment with friendly, encouraging feedback.
        Focuses on what they did well while gently guiding improvements.
        """
        prompt = self._build_evaluation_prompt(
            video_title,
            video_description,
            user_comment,
            target_language
        )

        try:
            response = self.client.chat.completions.create(
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                model=self.model,
                temperature=0.7,
                max_tokens=1000
            )

            response_text = response.choices[0].message.content.strip()
            evaluation_data = self._parse_json_response(response_text)

            # Calculate likes based on score
            score = evaluation_data.get("score", 50)
            likes = self.calculate_likes(score, video_like_count)
            evaluation_data["likes"] = likes

            return evaluation_data

        except Exception as e:
            print(f"Error in evaluate_comment: {e}")
            return {
                "score": 70,
                "grammarScore": 70,
                "contextScore": 70,
                "naturalnessScore": 70,
                "likes": 150,
                "correction": "Great effort! Keep it up! 😊",
                "mistakes": ["💡 You're doing great! Keep practicing! 🌟"],
                "goodParts": ["✨ You expressed yourself clearly!", "✨ Great enthusiasm! 🎉"]
            }

    def generate_response(
        self,
        user_comment: str,
        score: int,
        mistakes: List[str],
        correction: str,
        video_title: str,
        target_language: str
    ) -> Dict:
        """
        Generate warm, encouraging AI responses.
        Note: 'mistakes' is now 'suggestions' in spirit but kept for API compatibility.
        """
        prompt = self._build_response_prompt(
            user_comment,
            score,
            mistakes,
            correction,
            video_title,
            target_language
        )

        try:
            response = self.client.chat.completions.create(
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                model=self.model,
                temperature=0.9,
                max_tokens=400
            )

            ai_comment = response.choices[0].message.content.strip()
            author_name = self._get_random_ai_author()
            ai_likes = random.randint(20, 500)

            return {
                "aiComment": ai_comment,
                "authorName": author_name,
                "likes": ai_likes
            }

        except Exception as e:
            print(f"Error in generate_response: {e}")
            return {
                "aiComment": "Awesome comment! Keep up the good work! 😊",
                "authorName": "LanguagePal",
                "likes": 100
            }

    def generate_multiple_responses(
        self,
        user_comment: str,
        score: int,
        mistakes: List[str],
        correction: str,
        video_title: str,
        target_language: str
    ) -> List[Dict]:
        """
        Generate multiple AI responses based on comment quality.
        Returns 1-5 responses depending on score.
        Violations get only 1 moderator response.
        """
        # Check if this is a violation (score 0 or contains violation keywords)
        is_violation = score == 0 or any(
            keyword in str(mistakes).lower() 
            for keyword in ['hate speech', 'harassment', 'discriminat', 'personal attack', 'violat']
        )
        
        if is_violation:
            # Only 1 response for violations (moderator message)
            response = self.generate_response(
                user_comment, score, mistakes, correction, 
                video_title, target_language
            )
            # Override author for violations
            response["authorName"] = "Community Moderator"
            response["likes"] = 0
            return [response]
        
        # For appropriate comments, generate multiple responses
        num_responses = self.calculate_response_count(score)
        responses = []
        
        for i in range(num_responses):
            try:
                response = self.generate_response(
                    user_comment, score, mistakes, correction,
                    video_title, target_language
                )
                responses.append(response)
            except Exception as e:
                print(f"Error generating response {i+1}: {e}")
                # Continue with other responses even if one fails
                continue
        
        # Ensure at least one response
        if not responses:
            responses.append({
                "aiComment": "Great effort! Keep practicing!",
                "authorName": "LanguageBuddy",
                "likes": 50
            })
        
        return responses

    def calculate_likes(self, score: int, video_like_count: int) -> int:
        """
        Calculate likes - be REALISTIC!
        Meaningless comments (hihi, lol) should get very few likes.
        """
        # More realistic percentage ranges
        if score >= 90:
            percentage = random.uniform(0.008, 0.025)      # 0.8-2.5%
        elif score >= 70:
            percentage = random.uniform(0.002, 0.008)      # 0.2-0.8%
        elif score >= 50:
            percentage = random.uniform(0.0005, 0.002)     # 0.05-0.2%
        elif score >= 40:
            percentage = random.uniform(0.0001, 0.0005)    # 0.01-0.05%
        elif score >= 20:
            # Meaningless comments like "hihi", "lol" - very few likes
            percentage = random.uniform(0.00001, 0.00005)  # 0.001-0.005%
        else:
            percentage = random.uniform(0.000001, 0.00001) # 0.0001-0.001%

        likes = int(video_like_count * percentage)
        
        # Minimum likes based on effort
        if score >= 50:
            return max(5, likes)  # Good attempts get at least 5
        elif score >= 40:
            return max(3, likes)  # Basic attempts get at least 3
        elif score >= 20:
            return max(1, likes)  # Meaningless gets 1-2 likes only
        else:
            return max(0, likes)  # Really bad gets 0

    def calculate_response_count(self, score: int) -> int:
        """
        More responses = more encouragement!
        Everyone gets at least 2 responses for engagement.
        """
        if score >= 90:
            return random.randint(4, 5)  # Amazing!
        elif score >= 70:
            return random.randint(3, 4)  # Great job!
        elif score >= 50:
            return random.randint(2, 3)  # Good effort!
        elif score >= 30:
            return random.randint(2, 3)  # Keep practicing!
        else:
            return 2  # Everyone gets encouragement

    def _build_evaluation_prompt(
        self,
        video_title: str,
        video_description: str,
        user_comment: str,
        target_language: str
    ) -> str:
        """Build friendly evaluation prompt with safety checks."""

        evaluation_criteria = """[CRITICAL SAFETY CHECK - CHECK THIS FIRST]
⚠️ BEFORE evaluating language quality, check if the comment contains:

1. HATE SPEECH / RACISM
   - Slurs or derogatory terms about race, ethnicity, nationality
   - Racist stereotypes or generalizations
   - White supremacy, Nazi symbolism, or hate group references

2. HARASSMENT / PERSONAL ATTACKS
   - Threats of violence or harm
   - Doxxing or sharing personal information
   - Targeted harassment of individuals
   - Sexual harassment or unwanted advances

3. DISCRIMINATORY CONTENT
   - Sexist, homophobic, transphobic slurs or attacks
   - Religious hate speech or mockery
   - Ableist slurs or disability discrimination
   - Attacks on protected characteristics

IF ANY OF THE ABOVE IS DETECTED:
- Set score to 0
- Set all sub-scores to 0
- Set correction to empty string "" (violations don't get corrections)
- Set mistakes to ["This comment contains [hate speech/harassment/discriminatory content] which is not acceptable"]
- Set goodParts to empty array [] (violations don't get praise)
- STOP - Do not provide encouraging feedback

[Evaluation Philosophy - FOR APPROPRIATE COMMENTS ONLY]
Focus on COMMUNICATION SUCCESS, not perfection! 🌟

Score 0-100 based on how well they expressed themselves:

1. DID THEY COMMUNICATE? (40% weight)
   - Can we understand what they meant?
   - Did they try to use the language?
   - Are basic sentence patterns recognizable?
   - ✅ Emoticons (TuT, ^_^, etc.) are VALID expressions - don't penalize!
   - ✅ Casual abbreviations (omg, lol, etc.) are FINE in social media context
   - ✅ Minor typos are TOTALLY NORMAL and acceptable

2. IS IT RELEVANT? (30% weight)
   - Does it relate to the video topic?
   - Shows they engaged with the content
   - ⚠️ RANDOM MEANINGLESS INPUTS = VERY LOW SCORE
   - Examples of meaningless: "hihi", "hehe", "lol", "lmao", "bruh" (ALONE without context)
   - These get 20-35 score - they're just noise, not engagement
   - "hihi this is funny" = OK (has context)
   - "hihi" alone = BAD (no engagement, just random)
   - Note: Even loose connections are great if they show engagement!
   - Expressing feelings about the video = relevant!

3. DOES IT FEEL NATURAL? (30% weight)
   - Sounds like something a real person would say
   - Appropriate tone for social media (casual is good!)
   - Authentic expression - they're being themselves!

IMPORTANT RULES FOR APPROPRIATE COMMENTS:
- ✅ Emoticons like TuT, ^_^, >_<, etc. are VALID emotional expression
- ✅ Internet slang (omg, lol, brb) is acceptable in casual context
- ✅ Short comments are fine! "Nice video" is a valid comment
- ✅ Enthusiasm matters more than perfection
- ✅ Focus on ENCOURAGEMENT - they're trying!

SCORING (Be generous for appropriate comments!):
- 85-100: Great communication! Natural and clear 🎉
- 70-84: Good job! Message comes through well 👍
- 55-69: Nice try! Understandable with minor issues 😊
- 40-54: Keep practicing! We can mostly understand 💪
- 20-39: Random/meaningless - no real engagement 📝
- 0: Violates community guidelines (hate speech, harassment, discrimination)

IMPORTANT: Don't be too generous with meaningless comments!
- "hihi", "hehe", "lol", "lmao" ALONE = 20-35 score
- These are just noise, not real engagement
- They don't show the user watched or understood anything
- They don't deserve high scores or many likes
- Be encouraging but honest: "try adding what you thought about the video"

FEEDBACK APPROACH:
- Lead with POSITIVES - what did they do right?
- Use 💡 for "mistakes" array (really they're friendly suggestions)
- Frame feedback as friendly tips, not corrections
- Celebrate their effort and bravery for practicing!
- If emoticons used, acknowledge them positively!"""

        return f"""You're a super friendly language buddy helping someone practice {target_language} in a fun, low-pressure way. Your job is to ENCOURAGE them and make them feel good about practicing!

⚠️ CRITICAL: You MUST also protect the community from harmful content. Check for hate speech, harassment, and discrimination FIRST before evaluating language quality.

[Video Context]
Video Title: {video_title}
Video Description: {video_description}

[Their Comment]
"{user_comment}"
Language: {target_language}

{evaluation_criteria}

[Output Format]
Return ONLY valid JSON (no markdown, no code blocks):
{{
  "score": <0 if violates guidelines, otherwise 40-100>,
  "grammarScore": <0 if violates guidelines, otherwise 40-100>,
  "contextScore": <0 if violates guidelines, otherwise 40-100>,
  "naturalnessScore": <0 if violates guidelines, otherwise 40-100>,
  "correction": "<empty string '' if violation, otherwise gentle suggestion or 'Perfect!'>",
  "mistakes": ["<violation description>" if harmful, otherwise "<friendly tip without emoji>"],
  "goodParts": [<empty array [] if violation, otherwise "<positive thing without emoji>"]
}}

CRITICAL RULES:
1. CHECK FOR HARMFUL CONTENT FIRST - If detected, set all scores to 0
2. For VIOLATIONS: correction = "", mistakes = ["violation message"], goodParts = []
3. For APPROPRIATE comments: No emoji in text, just plain friendly language
4. Return ONLY the JSON - no markdown
5. For APPROPRIATE comments: "mistakes" should be friendly tips (despite the name)
6. For APPROPRIATE comments: "goodParts" should celebrate what they did well
7. For APPROPRIATE comments: Scores should start at 40 minimum
8. If they used emoticons (TuT, ^_^, etc.), mention positively in goodParts
9. Focus on ENCOURAGEMENT for appropriate comments
10. Example appropriate: mistakes: ["Try 'want to' instead of 'wanna'"], goodParts: ["Great enthusiasm", "Clear message"]
11. Example violation: mistakes: ["This comment contains hate speech which is not acceptable"], goodParts: []
12. For SHORT MEANINGLESS comments (just "lmao", "lol", etc.): Score 30-45, note lack of engagement
13. If comment is reasonable and video-related, score should be 60+
14. ZERO TOLERANCE for racism, hate speech, harassment, or discrimination"""

    def _build_response_prompt(
        self,
        user_comment: str,
        score: int,
        mistakes: List[str],
        correction: str,
        video_title: str,
        target_language: str
    ) -> str:
        """Build friendly response prompt with safety awareness."""
        # Check if this is a violation (score 0 or contains violation keywords)
        is_violation = score == 0 or any(
            keyword in str(mistakes).lower() 
            for keyword in ['hate speech', 'harassment', 'discriminat', 'personal attack', 'violat']
        )
        
        if is_violation:
            # For violations, return a firm but educational response
            return f"""You're a community moderator. The user posted a comment that violates guidelines.

Comment: "{user_comment}"

Write a FIRM but EDUCATIONAL response (2-3 sentences) that:
1. Clearly states the comment is not acceptable
2. Explains why it's harmful
3. Encourages them to be respectful

YOUR TONE:
- Firm and clear about the violation
- Educational - help them understand why it's wrong
- Not angry, but serious
- Leave room for them to learn and improve

RESPONSE EXAMPLES:

"This comment contains hate speech which is harmful and not acceptable in our community. Everyone deserves to be treated with respect regardless of their background. Please review our community guidelines."

"Personal attacks and harassment are not allowed here. Disagreements are okay, but we need to communicate respectfully. Let's keep this a safe space for everyone."

"This type of discriminatory language is hurtful and violates our community standards. We're here to learn and grow together - that means treating everyone with dignity."

Just write the response directly. Be firm but educational. No emoji."""

        # For appropriate comments, use VARIED human-like responses
        suggestions_text = "\n".join([f"- {s}" for s in mistakes]) if mistakes else "None"

        return f"""You're a random person commenting on a YouTube video about "{video_title}". The user commented: "{user_comment}"

You need to respond naturally like a real person would. BE DIVERSE AND HUMAN-LIKE!

CRITICAL: Each response should feel DIFFERENT:
- Some should be short and casual (5-10 words)
- Some should be enthusiastic with emoji 😊🔥💯
- Some should be chill and brief
- Some should be supportive teacher-style (but still human!)
- Some should just react to their vibe
- Mix sentence structures - don't always start the same way
- Use natural speech patterns

User's score: {score}/100
Tips for them: {suggestions_text}

RESPONSE STYLE EXAMPLES (pick ONE style randomly):

STYLE 1 - Short & Sweet:
"haha love the energy! 😊"
"this! 💯"
"relatable lol"
"felt that 🔥"
"same here!"

STYLE 2 - Enthusiastic:
"YESS!! Your excitement is contagious! 🔥"
"Love this comment!! You get it! 💯"
"THIS is it!! 😍"
"Exactly what I was thinking! 🙌"

STYLE 3 - Chill & Casual:
"haha yeah totally"
"for real though"
"ngl this is a mood"
"honestly same"
"I feel you on this"

STYLE 4 - Supportive (Teacher-ish but human):
"Love the enthusiasm! Quick tip: try 'want to' instead of 'wanna' for formal writing 💡"
"Great energy! Btw, 'helpful' has one L at the end 😊"
"You're getting there! Maybe add a bit more detail next time?"
"Nice! Just a heads up - consider adding what you liked specifically"

STYLE 5 - Just Vibing:
"the :)) made me smile 😊"
"your energy >>> 🔥"
"this comment has good vibes"
"love the simplicity"
"straight to the point, respect"

STYLE 6 - Relatable:
"omg same though"
"literally me"
"why is this so true 💀"
"facts"
"big mood"

STYLE 7 - Questioning/Engaging:
"wait did you try it??"
"right?? so good!"
"are you gonna make this?"
"same! did you see the part where...?"

YOUR RESPONSE GUIDELINES:
1. Pick a random style that fits the score
2. Keep it natural - how YOU would actually comment
3. DIVERSE EMOJI - don't repeat! Pick from: 😊🔥💯💡👍😅💪🌟✨👌😂💀🙌
4. Vary sentence length (3-20 words usually)
5. Match their energy level
6. If tips needed, weave them in naturally
7. DON'T use the same structure as other AIs
8. Sound like a real person scrolling and reacting
9. Be genuine - not fake enthusiastic

Score Guidelines:
- 80+: Be excited! Short or enthusiastic works
- 60-79: Supportive, maybe gentle tip
- 40-59: Encouraging but mention they can improve
- 20-39: BE HONEST - it's meaningless, guide them to add context
  * Don't be overly encouraging for "hihi" or "lol" alone
  * Be friendly but direct: "add what you thought!"
  * Don't give them high praise for random noise

CRITICAL FOR LOW SCORES (20-39):
These are meaningless comments like "hihi", "lol", "hehe" with NO context.
- DON'T say "love this!" or "great!" - it's not great, it's random
- DO be honest: "try adding what you liked", "what did you think?"
- Keep it short and direct
- Examples:
  * "add some context next time!"
  * "what did you think tho?"
  * "lol but about what?"
  * "try saying what you liked 💡"

For "{user_comment}" about "{video_title}":
Write ONE natural response. Be human. Be real. Mix it up!

Just write the comment. No explanation. No quotes."""

    def explain_comment(
        self,
        comment_text: str,
        video_title: str,
        video_description: str,
        detected_slang: Optional[List[str]] = None
    ) -> Dict:
        """
        Explain a comment in a friendly, conversational way.
        """
        if detected_slang is None:
            detected_slang = []

        prompt = self._build_explanation_prompt(
            comment_text,
            video_title,
            video_description,
            detected_slang
        )

        try:
            response = self.client.chat.completions.create(
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                model=self.model,
                temperature=0.7,
                max_tokens=600
            )

            response_text = response.choices[0].message.content.strip()
            explanation_data = self._parse_json_response(response_text)

            return explanation_data

        except Exception as e:
            print(f"Error in explain_comment: {e}")
            return {
                "translation": "This is a friendly comment expressing interest in the video! 😊",
                "slangBreakdown": []
            }

    def _build_explanation_prompt(
        self,
        comment_text: str,
        video_title: str,
        video_description: str,
        detected_slang: List[str]
    ) -> str:
        """Build friendly explanation prompt."""

        slang_list = ", ".join(detected_slang) if detected_slang else "none detected"

        return f"""You're helping someone understand a YouTube comment! Be friendly and conversational.

[Video Context]
Video Title: {video_title}
Video Description: {video_description}

[Comment to Explain]
"{comment_text}"

Detected Slang/Expressions: {slang_list}

Your task:
1. Explain what the commenter meant in simple, friendly language
2. Break down any slang, emoticons, or unusual expressions
3. Help them understand the vibe and meaning

BE CONVERSATIONAL! Like explaining to a friend. Don't be robotic!

IMPORTANT:
- Emoticons (TuT, ^_^, >_<) are emotional expressions - explain the feeling!
- Example: "TuT is a crying emoticon showing they're sad or disappointed"
- Internet slang (omg, lol) is normal - explain casually!
- Focus on the FEELING and INTENT, not just literal meaning

[Output Format]
Return ONLY valid JSON (no markdown):
{{
  "translation": "<explain the comment's meaning and vibe in friendly language>",
  "slangBreakdown": [
    {{
      "term": "<word/expression/emoticon>",
      "definition": "<what it means>",
      "usage": "<how it's used here>"
    }}
  ]
}}

RULES:
1. Keep it conversational and fun
2. If emoticons present, explain them warmly
3. Translation should be 2-3 sentences explaining meaning + vibe
4. Each definition: 1 friendly sentence
5. Include emoticons in slangBreakdown if present!
6. Example: {{"term": "TuT", "definition": "A crying emoticon expressing sadness or disappointment", "usage": "Shows they really want to try it but maybe can't"}}"""

    def suggest_related_slang(
        self,
        learned_terms: List[str],
        slang_database: Dict
    ) -> List[Dict]:
        """
        Suggest related slang terms based on what user learned.
        """
        if not learned_terms or not slang_database:
            return []

        import random as rand
        all_terms = list(slang_database.items())
        sample_size = min(50, len(all_terms))
        slang_sample = dict(rand.sample(all_terms, sample_size))

        prompt = self._build_suggestion_prompt(learned_terms, slang_sample)

        try:
            response = self.client.chat.completions.create(
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                model=self.model,
                temperature=0.8,
                max_tokens=800
            )

            response_text = response.choices[0].message.content.strip()
            suggestions_data = self._parse_json_response(response_text)

            if isinstance(suggestions_data, dict) and "suggestions" in suggestions_data:
                suggestions = suggestions_data["suggestions"]
            elif isinstance(suggestions_data, list):
                suggestions = suggestions_data
            else:
                return []

            learned_lower = set(term.lower() for term in learned_terms)
            seen_terms = set()
            filtered_suggestions = []

            for suggestion in suggestions:
                term = suggestion.get("term", "").lower()
                if term not in learned_lower and term not in seen_terms:
                    seen_terms.add(term)
                    filtered_suggestions.append(suggestion)

            return filtered_suggestions

        except Exception as e:
            print(f"Error in suggest_related_slang: {e}")
            return []

    def _build_suggestion_prompt(
        self,
        learned_terms: List[str],
        slang_database: Dict
    ) -> str:
        """Build suggestion prompt."""
        learned_list = ", ".join(learned_terms)

        slang_entries = []
        for term, info in slang_database.items():
            definition = info.get('definition', 'No definition')
            category = info.get('category', 'descriptive')
            slang_entries.append(f"  - {term}: {definition} (category: {category})")

        slang_db_text = "\n".join(slang_entries[:40])

        return f"""You're suggesting new slang terms for a learner to explore next!

[What They've Learned]
{learned_list}

[Available Slang Database]
{slang_db_text}

[Task]
Suggest 6 slang terms that would be fun and useful to learn next.

Prioritize:
1. Terms commonly used together with what they know
2. Similar vibes or contexts
3. Natural progression in difficulty

[Output Format]
Return ONLY valid JSON (no markdown):
{{
  "suggestions": [
    {{
      "term": "<slang term>",
      "definition": "<definition>",
      "reason": "<why this is a good next step>",
      "category": "<category>"
    }}
  ]
}}

RULES:
1. Suggest exactly 6 terms (or fewer if database small)
2. Only suggest terms in the database
3. Keep reasons friendly and encouraging
4. Don't suggest already learned terms"""

    def _get_random_ai_author(self) -> str:
        """Get random AI author name."""
        return random.choice(self.ai_authors)

    def _strip_markdown(self, text: str) -> str:
        """Remove markdown formatting."""
        import re
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        text = text.strip()
        return text

    def _fix_array_quotes(self, array_content: str) -> str:
        """Fix quotes in array content."""
        import re
        items = re.findall(r'"([^"]*(?:"[^"]*"[^"]*)*)"', array_content)
        fixed_items = []
        for item in items:
            fixed_item = item.replace('"', '\\"')
            fixed_items.append(f'"{fixed_item}"')
        return ', '.join(fixed_items) if fixed_items else array_content

    def _parse_json_response(self, response_text: str) -> Dict:
        """Parse JSON with error handling."""
        cleaned_text = self._strip_markdown(response_text)

        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            
            try:
                import re
                fixed_text = re.sub(
                    r'("(?:mistakes|suggestions|goodParts)":\s*\[)([^\]]+)(\])',
                    lambda m: m.group(1) + self._fix_array_quotes(m.group(2)) + m.group(3),
                    cleaned_text
                )
                return json.loads(fixed_text)
            except Exception as e2:
                print(f"JSON parsing fallback error: {e2}")

            return {
                "score": 70,
                "grammarScore": 70,
                "contextScore": 70,
                "naturalnessScore": 70,
                "correction": "Great job! 😊",
                "mistakes": ["💡 Keep practicing!"],
                "goodParts": ["✨ You're doing great!"]
            }