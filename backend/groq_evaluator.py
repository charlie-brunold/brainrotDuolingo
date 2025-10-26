# groq_evaluator.py

import os
import json
import random
from typing import Dict, List, Optional
from groq import Groq

class GroqCommentEvaluator:
    """
    Evaluates user comments on videos using Groq AI and generates engaging responses.
    Implements the two-stage evaluation system from GROQ_INTEGRATION_DESIGN.md
    """

    def __init__(self, api_key: str):
        """
        Initialize the Groq evaluator with API credentials.

        Args:
            api_key: Groq API key
        """
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"

        # AI personality author names for responses
        self.ai_authors = [
            "LinguaLegend",
            "GrammarGoddess",
            "SyntaxSavage",
            "VocabVibes",
            "LanguageLord",
            "FluentFiend",
            "WordWizard",
            "PhrasePhenom",
            "LexiconLegacy",
            "DialectDemon"
        ]

    def evaluate_comment(
        self,
        video_title: str,
        video_description: str,
        user_comment: str,
        target_language: str,
        video_like_count: int,
        available_slang: List[str] = None
    ) -> Dict:
        """
        Evaluate a user's comment with detailed scoring and feedback.

        Args:
            video_title: Title of the video being commented on
            video_description: Description of the video
            user_comment: The user's comment to evaluate
            target_language: Language being learned (e.g., "English", "Spanish")
            video_like_count: Number of likes on the video (for like calculation)
            available_slang: List of slang terms available in the video

        Returns:
            Dictionary with score, likes, feedback, and detailed breakdown
        """
        # Detect which slang terms user attempted to use
        if available_slang is None:
            available_slang = []

        detected_slang = self._detect_slang_in_comment(user_comment, available_slang)

        # Construct evaluation prompt with slang focus
        prompt = self._build_evaluation_prompt(
            video_title,
            video_description,
            user_comment,
            target_language,

        )

        try:
            # Call Groq with evaluation parameters
            response = self.client.chat.completions.create(
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                model=self.model,
                temperature=0.7,  # Balance between consistent and natural
                max_tokens=1000   # Enough for detailed JSON response
            )

            # Parse the response
            response_text = response.choices[0].message.content.strip()
            evaluation_data = self._parse_json_response(response_text)

            # Calculate social validation (likes) based on score
            score = evaluation_data.get("score", 0)
            likes = self.calculate_likes(score, video_like_count)
            evaluation_data["likes"] = likes

            return evaluation_data

        except Exception as e:
            print(f"Error in evaluate_comment: {e}")
            # Return fallback response
            return {
                "score": 50,
                "grammarScore": 50,
                "contextScore": 50,
                "naturalnessScore": 50,
                "likes": 100,
                "correction": "Keep practicing!",
                "mistakes": ["Oops, had trouble processing that - try again!"],
                "goodParts": ["You're making an effort!"]
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
        Generate a warm, encouraging AI response with teacher personality.

        Args:
            user_comment: The user's original comment
            score: The evaluation score (0-100)
            mistakes: List of suggestions for improvement (kept as 'mistakes' for compatibility)
            correction: The corrected version of the comment
            video_title: Title of the video
            target_language: Language being learned

        Returns:
            Dictionary with AI comment, author name, and likes
        """
        # Construct response prompt
        prompt = self._build_response_prompt(
            user_comment,
            score,
            mistakes,
            correction,
            video_title,
            target_language
        )

        try:
            # Call Groq with response parameters
            response = self.client.chat.completions.create(
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                model=self.model,
                temperature=0.9,  # Higher temp for creative/funny responses
                max_tokens=400    # Short response only
            )

            # Get plain text response
            ai_comment = response.choices[0].message.content.strip()

            # Generate metadata
            author_name = self._get_random_ai_author()
            ai_likes = random.randint(10, 500)  # Random engagement on AI comment

            return {
                "aiComment": ai_comment,
                "authorName": author_name,
                "likes": ai_likes
            }

        except Exception as e:
            print(f"Error in generate_response: {e}")
            return {
                "aiComment": "Oops, couldn't generate a response rn 😅 Try again!",
                "authorName": "LanguageBot",
                "likes": 42
            }

    def calculate_likes(self, score: int, video_like_count: int) -> int:
        """
        Calculate user comment likes as a percentage of the video's like count.
        Users get a small fraction of what the video itself received, based on score quality.

        Score Tiers:
        - 90-100: Viral comment (0.5-2% of video likes)
        - 70-89:  Popular comment (0.1-0.5% of video likes)
        - 50-69:  Decent comment (0.01-0.1% of video likes)
        - 30-49:  Weak comment (0.001-0.01% of video likes)
        - 0-29:   Poor comment (0.0001-0.001% of video likes)

        Args:
            score: Evaluation score (0-100)
            video_like_count: Number of likes on the video

        Returns:
            Calculated like count (minimum 0 for scores below 30)
        """
        # Define realistic percentage ranges for each tier
        if score >= 90:
            percentage = random.uniform(0.005, 0.02)      # 0.5-2%
        elif score >= 70:
            percentage = random.uniform(0.001, 0.005)     # 0.1-0.5%
        elif score >= 50:
            percentage = random.uniform(0.0001, 0.001)    # 0.01-0.1%
        elif score >= 30:
            percentage = random.uniform(0.00001, 0.0001)  # 0.001-0.01%
        else:
            percentage = random.uniform(0.000001, 0.00001) # 0.0001-0.001%

        # Calculate likes (allow 0 for very poor comments)
        likes = int(video_like_count * percentage)
        return max(0, likes)

    def calculate_response_count(self, score: int) -> int:
        """
        Determine how many AI responses to generate based on comment score.
        Higher scores = more engagement/social validation from the community.

        Score Tiers:
        - 90-100: Fire comment (4-5 responses - everyone's hyping you up!)
        - 70-89:  Solid comment (3-4 responses - good engagement)
        - 50-69:  Mid comment (2-3 responses - moderate engagement)
        - 30-49:  Struggling comment (1-2 responses - minimal engagement)
        - 0-29:   Yikes comment (1 response - single reality check)

        Args:
            score: Evaluation score (0-100)

        Returns:
            Number of AI responses to generate (1-5)
        """
        if score >= 90:
            return random.randint(4, 5)  # Fire = everyone responds
        elif score >= 70:
            return random.randint(3, 4)  # Solid = good engagement
        elif score >= 50:
            return random.randint(2, 3)  # Mid = moderate
        elif score >= 30:
            return random.randint(1, 2)  # Struggling = minimal
        else:
            return 1  # Yikes = single roast

    def _detect_slang_in_comment(self, user_comment: str, available_slang: List[str]) -> List[str]:
        """
        Detect which slang terms from the available list appear in the user's comment.
        Uses word boundary matching to avoid false positives.

        Args:
            user_comment: The user's comment text
            available_slang: List of slang terms to check for

        Returns:
            List of detected slang terms
        """
        import re
        detected = []
        comment_lower = user_comment.lower()

        for slang in available_slang:
            # Use word boundary regex to match whole words only
            pattern = r'\b' + re.escape(slang.lower()) + r'\b'
            if re.search(pattern, comment_lower):
                detected.append(slang)

        return detected

    def _build_evaluation_prompt(
        self,
        video_title: str,
        video_description: str,
        user_comment: str,
        target_language: str,
        available_slang: List[str] = None,
        detected_slang: List[str] = None
    ) -> str:
        """Build the evaluation prompt with focus on cultural adaptation and communication effectiveness."""

        if available_slang is None:
            available_slang = []
        if detected_slang is None:
            detected_slang = []

        # Build slang context section
        slang_context = ""
        if available_slang:
            slang_list = ", ".join(available_slang)
            slang_context = f"\n[Cultural Context]\nCommon expressions in this video: {slang_list}\n"

            if detected_slang:
                detected_list = ", ".join(detected_slang)
                slang_context += f"User incorporated: {detected_list}\n"

        # Unified evaluation criteria focusing on overall communication
        evaluation_criteria = """[Evaluation Criteria]
Score 0-100 based on how naturally the user communicates on social media:

1. CONTEXT RELEVANCE (30% weight) - Does it relate to the video?
   - Shows they watched and understood the content
   - Responds to something from the video
   - Note: Even loose connections are fine - this is social media!

2. TONE & NATURALNESS (30% weight) - Does it sound like a real comment?
   - Casual and conversational (formal is okay too, just different style)
   - Natural phrasing for the platform
   - Authentic expression
   - IMPORTANT: Slang is NOT required! Natural language without slang is perfectly fine

3. CLARITY (25% weight) - Can people understand it?
   - Main idea comes through
   - Makes sense to readers
   - Word choices work

4. LANGUAGE ACCURACY (15% weight) - Basic communication
   - Note: Perfect grammar NOT needed - this is social media!
   - Only flag things that really confuse the message
   - Typos and casual shortcuts are totally normal

SCORING GUIDANCE (be generous!):
- 85-100: Totally natural comment - fits right in (with or without slang)
- 70-84: Good comment with personality
- 50-69: Decent comment, maybe a bit awkward
- 30-49: Understandable but feels off
- 0-29: Hard to understand OR completely random/unrelated

CRITICAL - ABOUT SLANG:
- Do NOT penalize for lack of slang usage
- Do NOT suggest adding slang unless it's really natural for that context
- Many great comments use zero slang - that's totally fine!
- Only mention slang if they used it incorrectly
- Focus on natural communication, not slang usage

MODIFIERS:
- Short comments (under 5 words): No penalty! Short comments are super common
- Random comment with zero connection to video: Only then apply -20 penalty
- BE LENIENT: This is social media, not an essay. Casual = good!

IMPORTANT - KEEP FEEDBACK LIGHT:
- In the "mistakes" array, frame everything as friendly tips
- Maximum 2-3 tips - don't overwhelm them
- If off-topic, casually mention what the video is about: ["btw this video is about cooking tips"]
- Focus on helping them sound natural, not adding slang"""

        return f"""You are a chill, friendly language coach helping someone learn to comment naturally on social media in {target_language}. You're here to help them fit in and communicate effectively. Natural language without slang is perfectly fine - don't push slang usage!

[Video Context]
Video Title: {video_title}
Video Description: {video_description}
{slang_context}
[User's Comment]
Comment: {user_comment}
Target Language: {target_language}

{evaluation_criteria}

[Output Format]
Return ONLY valid JSON with no markdown formatting, no code blocks, no backticks:
{{
  "score": <0-100>,
  "grammarScore": <0-100>,
  "contextScore": <0-100>,
  "naturalnessScore": <0-100>,
  "correction": "<improved version that sounds more natural, or 'Looks good!' if already natural>",
  "mistakes": ["<friendly tip 1>", "<friendly tip 2>"],
  "goodParts": ["<positive observation 1>", "<positive observation 2>"]
}}

CRITICAL JSON RULES:
1. Return ONLY the JSON object - no markdown, no code blocks, no backticks
2. The "mistakes" field should contain FRIENDLY, CASUAL TIPS - not harsh corrections
3. Think of it as chatting with a friend, not grading a test
4. Keep tips light and encouraging - this is social media, not an exam
5. DO NOT suggest adding slang unless it's truly natural for that context
6. Natural comments without slang deserve high scores too!
7. Each array item MUST be a properly quoted JSON string
8. Inside array strings, avoid using quotes - instead of "word" should be "correction", write: word should be correction
9. Example friendly tips format: ["could add more details about what you liked", "btw this video is about travel tips", "the phrasing could be more natural"]
10. Example goodParts format: ["clear and easy to understand", "sounds natural", "good connection to the video"]
11. All strings must be wrapped in double quotes per JSON spec
12. Keep it chill - social media is casual, so feedback should be too
13. MAXIMUM 2-3 tips total - don't overwhelm them with a long list
14. Only mention slang if they used it incorrectly - don't push slang usage"""


    def _build_response_prompt(
        self,
        user_comment: str,
        score: int,
        mistakes: List[str],
        correction: str,
        video_title: str,
        target_language: str
    ) -> str:
        """Build the warm, encouraging teacher-style response prompt."""
        suggestions_text = "\n".join([f"- {m}" for m in mistakes]) if mistakes else "None"

        return f"""You're a friendly language teacher commenting on social media. You sound like a normal person who happens to be good at teaching - approachable and helpful. Keep your language simple and natural, not overly trendy or Gen Z. DO NOT force slang into your responses!

Context:
- Post: "{video_title}"
- Their comment: "{user_comment}"
- Suggestions for improvement: {suggestions_text}
- Better version: {correction}

Write a SHORT comment (1-2 sentences max) responding to their comment.

YOUR TONE:
- Warm and encouraging, like a supportive friend
- Natural and conversational - just a regular person helping out
- Avoid heavy slang or Gen Z language (no "fr", "lowkey", "ngl", etc.)
- Use complete words, minimal abbreviations
- Make them feel good while offering gentle guidance
- Frame any corrections as helpful suggestions, not mistakes
- IMPORTANT: Don't use slang keywords unless they naturally fit - speak normally!

RESPONSE STYLE EXAMPLES (NO FORCED SLANG):

"Nice work! Just a small note - it should be 'learned' instead of 'learning' here."

"You're getting better at this! One thing: 'helpful' only has one L at the end."

"Good comment! For this context, 'era' would work better than 'estaba'."

"This sounds really natural - well done!"

"Great job working that expression into your comment naturally!"

"I can tell you're thinking about the grammar, which is awesome! Just remember 'a lot' is two words."

"This is really coming along - the structure is much more natural now."

"Perfect tone for this kind of video - you nailed it!"

"Almost perfect! Just change 'I learning' to 'I learned' and it's great."

"Really nice casual style here - keep practicing!"

Just respond with the comment. No explanation, no quotes around it, no meta-commentary. Speak like a normal person, not someone trying to sound cool with slang."""

    def _parse_json_response(self, response_text: str) -> Dict:
        """
        Parse JSON response with robust error handling.
        Strips markdown code blocks if present and attempts multiple parsing strategies.

        Args:
            response_text: Raw response text from LLM

        Returns:
            Parsed JSON dictionary
        """
        # Strip markdown code blocks if present
        cleaned_text = self._strip_markdown(response_text)

        # Try direct parsing first
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            print(f"JSON parsing error (attempt 1): {e}")

            # Attempt 2: Try to fix common issues with unescaped quotes in strings
            # Replace single quotes inside double-quoted strings with escaped quotes
            try:
                # Use regex to find and fix unescaped quotes in array values
                import re
                # Fix patterns like ["text with "quote" in it"]
                fixed_text = re.sub(
                    r'("(?:mistakes|suggestions|goodParts)":\s*\[)([^\]]+)(\])',
                    lambda m: m.group(1) + self._fix_array_quotes(m.group(2)) + m.group(3),
                    cleaned_text
                )
                return json.loads(fixed_text)
            except Exception as e2:
                print(f"JSON parsing error (attempt 2): {e2}")

            # Attempt 3: Try using ast.literal_eval as fallback
            try:
                import ast
                # Replace single quotes with double quotes for ast
                ast_text = cleaned_text.replace("'", '"')
                result = ast.literal_eval(ast_text)
                if isinstance(result, dict):
                    return result
            except Exception as e3:
                print(f"AST parsing error (attempt 3): {e3}")

            print(f"Original response text:\n{cleaned_text}")
            # Return fallback structure
            return {
                "score": 50,
                "grammarScore": 50,
                "contextScore": 50,
                "naturalnessScore": 50,
                "correction": "Keep it up!",
                "mistakes": ["Something went wrong - give it another shot!"],
                "goodParts": ["Nice try!"]
            }

    def _fix_array_quotes(self, array_content: str) -> str:
        """
        Fix unescaped quotes in array string values.
        Uses a simpler approach: find all items between commas and escape internal quotes.
        """
        import re

        # Split by ", " pattern to get individual items
        # But we need to be careful not to split on commas inside quotes

        # Simple approach: just escape all quotes that appear between array item boundaries
        # Pattern: match content between [" and "], handling internal quotes
        fixed_content = array_content

        # Find all string items in the array (between quotes)
        # Use a more aggressive approach: split on '", "' pattern
        if '", "' in array_content:
            parts = array_content.split('", "')
            fixed_parts = []

            for i, part in enumerate(parts):
                # Remove leading/trailing quotes from first/last parts
                if i == 0:
                    part = part.lstrip('"')
                if i == len(parts) - 1:
                    part = part.rstrip('"')

                # Escape any remaining quotes
                part = part.replace('"', '\\"')
                fixed_parts.append(part)

            fixed_content = '"' + '", "'.join(fixed_parts) + '"'
        else:
            # Single item or different format - just escape quotes
            fixed_content = array_content.replace('"', '\\"').replace('\\"', '"', 1)  # Keep first quote
            if fixed_content.endswith('\\"'):
                fixed_content = fixed_content[:-2] + '"'  # Keep last quote

        return fixed_content

    def _strip_markdown(self, text: str) -> str:
        """
        Remove markdown code block formatting from text.
        Handles cases like: ```json ... ``` or ``` ... ```

        Args:
            text: Text that may contain markdown

        Returns:
            Cleaned text without markdown
        """
        text = text.strip()

        # Check if wrapped in code blocks
        if text.startswith("```"):
            # Remove opening ```
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]  # Remove first line with ```json or ```

            # Remove closing ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            text = "\n".join(lines)

        return text.strip()

    def _get_random_ai_author(self) -> str:
        """
        Get a random AI author name for personality.

        Returns:
            Random author name from predefined list
        """
        return random.choice(self.ai_authors)

    def generate_random_username(self) -> str:
        """
        Generate a random Gen Z style username using Groq AI.

        Returns:
            A creative, Gen Z style username
        """
        prompt = """Generate a single creative username.

Examples of the style:
- sillySalmon728
- Jonathan.Doe
- rizzMaster3000
- RussianMonk14
- charliebrunold
- coolguy12345
- knannsbb2ll

Requirements:
- Creative and unique
- A concious choice between either camel case, snake case, lowercase, or uppercase
- A username with special personality that a Gen Z user would pick
- 8-15 characters

Output ONLY the username with no explanation or punctuation."""

        try:
            response = self.client.chat.completions.create(
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                model=self.model,
                temperature=0.95,  # High creativity for variety
                max_tokens=20      # Just need the username
            )

            username = response.choices[0].message.content.strip()
            # Remove any quotes or extra characters
            username = username.replace('"', '').replace("'", '').strip()

            # Validate it's reasonable (not empty, not too long)
            if username and len(username) <= 20 and username.isalnum():
                return username
            else:
                # Fallback to predefined list if invalid
                return self._get_random_ai_author()

        except Exception as e:
            print(f"Error generating username: {e}")
            # Fallback to predefined list
            return self._get_random_ai_author()

    def generate_multiple_responses(
        self,
        user_comment: str,
        score: int,
        mistakes: List[str],
        correction: str,
        video_title: str,
        target_language: str,
        available_slang: List[str] = None,
        num_responses: int = None
    ) -> List[Dict]:
        """
        Generate multiple AI responses from different "users" with varied perspectives.

        Args:
            user_comment: The user's original comment
            score: The evaluation score (0-100)
            mistakes: List of identified mistakes
            correction: The corrected version of the comment
            video_title: Title of the video
            target_language: Language being learned
            available_slang: Slang terms available in the video
            num_responses: Number of responses to generate (2-4, random if None)

        Returns:
            List of dictionaries with aiComment, authorName, and likes
        """
        # Detect slang usage
        if available_slang is None:
            available_slang = []

        detected_slang = self._detect_slang_in_comment(user_comment, available_slang)

        # Calculate response count based on score if not specified
        if num_responses is None:
            num_responses = self.calculate_response_count(score)
        else:
            num_responses = max(1, min(5, num_responses))  # Clamp between 1-5

        responses = []

        for i in range(num_responses):
            try:
                # Generate username first
                username = self.generate_random_username()

                # Construct prompt with variation for each response
                prompt = self._build_varied_response_prompt(
                    user_comment,
                    score,
                    mistakes,
                    correction,
                    video_title,
                    target_language,
                    available_slang,
                    detected_slang,
                    response_index=i
                )

                # Call Groq for this response
                response = self.client.chat.completions.create(
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }],
                    model=self.model,
                    temperature=0.9 + (i * 0.02),  # Slightly vary temperature for diversity
                    max_tokens=200
                )

                ai_comment = response.choices[0].message.content.strip()
                ai_likes = random.randint(10, 500)

                responses.append({
                    "aiComment": ai_comment,
                    "authorName": username,
                    "likes": ai_likes
                })

            except Exception as e:
                print(f"Error generating response {i+1}: {e}")
                # Add fallback response
                responses.append({
                    "aiComment": "Couldn't load this comment rn 😅",
                    "authorName": self._get_random_ai_author(),
                    "likes": random.randint(5, 50)
                })

        return responses

    def _build_varied_response_prompt(
        self,
        user_comment: str,
        score: int,
        mistakes: List[str],
        correction: str,
        video_title: str,
        target_language: str,
        available_slang: List[str],
        detected_slang: List[str],
        response_index: int
    ) -> str:
        """Build a natural response prompt without forced personality."""
        
        mistakes_text = "\n".join([f"- {m}" for m in mistakes]) if mistakes else "None"
        
        # Build minimal slang context - don't label it as "detected" or "available"
        slang_context = ""
        if detected_slang:
            slang_context = f"\nSlang in their comment: {', '.join(detected_slang)}"
        if available_slang and not detected_slang:
            # Only show available slang if they didn't use any
            slang_context = f"\nCommon slang for this: {', '.join(available_slang[:2])}"

        # Simple variation without personality engineering
        response_styles = [
        "React with minimal words - one or two words plus maybe an emoji.",
        "Point out one specific thing that caught your attention, ignore everything else.",
        "Ask a question instead of making a statement.",
        "Focus only on whether it worked or not, skip the explanation.",
        "React to their energy/vibe, not the technical mistakes.",
        "Be deadpan - state what's wrong like it's obvious.",
        "Give props if deserved, but make it understated.",
        "Use their own words back at them with correction.",
        "If there's slang, only comment on that - nothing else matters.",
        "Ignore any mistakes and just vibe with the content of what they said.",
        "Be blunt about what's wrong but keep it light.",
        "React like you're genuinely surprised (positive or negative).",
        ]
        
        style_hint = response_styles[response_index % len(response_styles)]

        return f"""You're scrolling comments and you're fluent in {target_language}. You comment like a regular person, not a language teacher.

Post: "{video_title}"
Their comment: "{user_comment}"
Mistakes: {mistakes_text}
Correction: {correction}{slang_context}

{style_hint}

Examples of natural responses:

"*learned"
"wait this is actually good"
"bro 💀"
"nah you cooked"
"okay the slang hit different"
"helpfull??"
"'alot' is crazy but go off"
"fr this is clean"
"almost perfect but it's 'era' not 'estaba'"
"you really said bussin unironically"
"could've used some slang tbh"
"this works"
"my guy forgot how to spell"
"okay okay I see you"
"'I learning' - bro"
"fire comment ngl"
"that's not how you use that slang lol"

Just write the comment (1-2 sentences max). Nothing else."""

    def explain_comment(
        self,
        comment_text: str,
        video_title: str,
        video_description: str,
        detected_slang: List[str] = None
    ) -> Dict:
        """
        Explain a YouTube comment by translating it to simpler language
        and breaking down each slang term with definitions and usage examples.

        Args:
            comment_text: The comment to explain
            video_title: Title of the video for context
            video_description: Description of the video for context
            detected_slang: List of slang terms detected in the comment

        Returns:
            Dictionary with translation and slangBreakdown
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
                "translation": "Could not generate explanation",
                "slangBreakdown": []
            }

    def _build_explanation_prompt(
        self,
        comment_text: str,
        video_title: str,
        video_description: str,
        detected_slang: List[str]
    ) -> str:
        """Build the prompt for explaining a comment with slang."""

        slang_list = ", ".join(detected_slang) if detected_slang else "none detected"

        return f"""You're helping someone learn slang by explaining a YouTube comment.

[Video Context]
Video Title: {video_title}
Video Description: {video_description}

[Comment to Explain]
"{comment_text}"

Detected Slang Terms: {slang_list}

Your task:
1. Paraphrase the comment into simple, clear language without any slang. Don't translate word for word, moreso describe the type of thing that the commenter was trying to get at with their comment
2. For each slang term, provide a definition and show how it's used in this specific context

ACT CONVERSATIONAL, like you're describing this to a friend. Your responses shouldn't feel rigid or contrived. The magic of your response is that it is disarming and helpful for learning objectives.

Keep it concise - this will be shown in a small tooltip.

[Output Format]
Return ONLY valid JSON with no markdown formatting, no code blocks, no backticks:
{{
  "translation": "<the comment rewritten in simple language without slang>",
  "slangBreakdown": [
    {{
      "term": "<slang term>",
      "definition": "<what it means>",
      "usage": "<how it's used in this comment>"
    }}
  ]
}}

CRITICAL JSON RULES:
1. Return ONLY the JSON object - no markdown, no code blocks, no backticks
2. Keep paraphrased section to 2-3 sentences max
3. Keep each definition to 1 sentence
4. Keep each usage to 1 sentence showing context
5. All strings must be wrapped in double quotes
6. If no slang detected, return empty slangBreakdown array"""

    def suggest_related_slang(
        self,
        learned_terms: List[str],
        slang_database: Dict
    ) -> List[Dict]:
        """
        Use AI to suggest related slang terms based on what the user has already learned.
        Focuses on terms that are commonly used together or in similar contexts.

        Args:
            learned_terms: List of slang terms the user has already learned
            slang_database: Dictionary of all available slang terms with their definitions

        Returns:
            List of suggested slang dictionaries with term, definition, reason, and category
        """
        if not learned_terms or not slang_database:
            # Return empty if no data to work with
            return []

        # Prepare slang database excerpt for the prompt (limit to 50 random terms to avoid token limits)
        import random as rand
        all_terms = list(slang_database.items())
        sample_size = min(50, len(all_terms))
        slang_sample = dict(rand.sample(all_terms, sample_size))

        # Build prompt for AI suggestions
        prompt = self._build_suggestion_prompt(learned_terms, slang_sample)

        try:
            response = self.client.chat.completions.create(
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                model=self.model,
                temperature=0.8,  # Creative but not too random
                max_tokens=800
            )

            response_text = response.choices[0].message.content.strip()
            suggestions_data = self._parse_json_response(response_text)

            # Validate and extract suggestions array
            if isinstance(suggestions_data, dict) and "suggestions" in suggestions_data:
                suggestions = suggestions_data["suggestions"]
            elif isinstance(suggestions_data, list):
                suggestions = suggestions_data
            else:
                print(f"Unexpected suggestion response format: {suggestions_data}")
                return []

            # Filter out learned terms and duplicates (case-insensitive)
            learned_lower = set(term.lower() for term in learned_terms)
            seen_terms = set()
            filtered_suggestions = []

            for suggestion in suggestions:
                term = suggestion.get("term", "").lower()
                # Skip if already learned or duplicate in suggestions
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
        """Build the prompt for suggesting related slang terms."""

        learned_list = ", ".join(learned_terms)

        # Format slang database for prompt (show term: definition pairs)
        slang_entries = []
        for term, info in slang_database.items():
            definition = info.get('definition', 'No definition')
            category = info.get('category', 'descriptive')
            slang_entries.append(f"  - {term}: {definition} (category: {category})")

        slang_db_text = "\n".join(slang_entries[:40])  # Limit to prevent token overflow

        return f"""You are a Gen Z slang expert analyzing a learner's vocabulary to suggest related terms.

[What They've Learned]
{learned_list}

[Available Slang Database]
{slang_db_text}

[Task]
Suggest 6 slang terms from the database that would be most valuable for them to learn next.

Prioritize terms that are:
1. COMMONLY USED TOGETHER with their learned terms (e.g., "rizz" often appears with "aura", "sigma")
2. IN SIMILAR CATEGORIES or contexts (e.g., if they learned positive vibes slang, suggest more positive vibes)
3. LOGICAL PROGRESSION from what they know (don't jump to super niche terms)

[Output Format]
Return ONLY valid JSON with no markdown formatting, no code blocks, no backticks:
{{
  "suggestions": [
    {{
      "term": "<slang term from database>",
      "definition": "<definition from database>",
      "reason": "<1 sentence explaining why this pairs well with what they've learned>",
      "category": "<category from database>"
    }}
  ]
}}

CRITICAL JSON RULES:
1. Return ONLY the JSON object - no markdown, no code blocks, no backticks
2. Suggest exactly 6 terms (or fewer if database is small)
3. Only suggest terms that exist in the provided database
4. Keep reason to 1 sentence (e.g., "Often used with rizz in dating contexts")
5. All strings must be wrapped in double quotes
6. DO NOT suggest terms they've already learned"""