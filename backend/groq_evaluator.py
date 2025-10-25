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
        video_view_count: int
    ) -> Dict:
        """
        Evaluate a user's comment with detailed scoring and feedback.

        Args:
            video_title: Title of the video being commented on
            video_description: Description of the video
            user_comment: The user's comment to evaluate
            target_language: Language being learned (e.g., "English", "Spanish")
            video_view_count: Number of views on the video (for like calculation)

        Returns:
            Dictionary with score, likes, feedback, and detailed breakdown
        """
        # Construct evaluation prompt
        prompt = self._build_evaluation_prompt(
            video_title,
            video_description,
            user_comment,
            target_language
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
            likes = self.calculate_view_based_likes(score, video_view_count)
            evaluation_data["likes"] = likes

            return evaluation_data

        except Exception as e:
            print(f"Error in evaluate_comment: {e}")
            # Return fallback response
            return {
                "score": 0,
                "grammarScore": 0,
                "contextScore": 0,
                "naturalnessScore": 0,
                "likes": 0,
                "correction": "Error processing comment",
                "mistakes": [f"System error: {str(e)}"],
                "goodParts": []
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
        Generate a Gen Z style AI response with roast-with-love personality.

        Args:
            user_comment: The user's original comment
            score: The evaluation score (0-100)
            mistakes: List of identified mistakes
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
                max_tokens=200    # Short response only
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

    def calculate_view_based_likes(self, score: int, video_view_count: int) -> int:
        """
        Calculate likes as a percentage of video views based on score tier.
        Uses realistic social media engagement rates.

        Score Tiers:
        - 90-100: Super viral (0.01-0.1% of views)
        - 80-89:  Viral (0.005-0.01% of views)
        - 70-79:  Popular (0.001-0.005% of views)
        - 60-69:  Above average (0.0005-0.001% of views)
        - 50-59:  Average (0.0001-0.0005% of views)
        - 40-49:  Below average (0.00005-0.0001% of views)
        - 0-39:   Poor (0.00001-0.00005% of views)

        Args:
            score: Evaluation score (0-100)
            video_view_count: Number of views on the video

        Returns:
            Calculated like count (minimum 1)
        """
        # Define realistic percentage ranges for each tier
        if score >= 90:
            percentage = random.uniform(0.0001, 0.001)      # 0.01-0.1%
        elif score >= 80:
            percentage = random.uniform(0.00005, 0.0001)    # 0.005-0.01%
        elif score >= 70:
            percentage = random.uniform(0.00001, 0.00005)   # 0.001-0.005%
        elif score >= 60:
            percentage = random.uniform(0.000005, 0.00001)  # 0.0005-0.001%
        elif score >= 50:
            percentage = random.uniform(0.000001, 0.000005) # 0.0001-0.0005%
        elif score >= 40:
            percentage = random.uniform(0.0000005, 0.000001)  # 0.00005-0.0001%
        else:
            percentage = random.uniform(0.0000001, 0.0000005) # 0.00001-0.00005%

        # Calculate likes and ensure minimum of 1
        likes = int(video_view_count * percentage)
        return max(1, likes)

    def _build_evaluation_prompt(
        self,
        video_title: str,
        video_description: str,
        user_comment: str,
        target_language: str
    ) -> str:
        """Build the evaluation prompt following design doc specifications."""
        return f"""You are a language learning evaluator. Analyze this user's comment.

[Video Context]
Video Title: {video_title}
Video Description: {video_description}

[User Input]
Comment: {user_comment}
Target Language: {target_language}

[Evaluation Criteria]
Score 0-100 based on:
1. Grammar/accuracy (50% weight) - Most important for language learning
2. Relevance to video (30% weight) - Ensures comprehension, not just translation
3. Vocabulary/naturalness (20% weight) - Rewards idiomatic usage

[Output Format]
Return ONLY valid JSON with no markdown formatting, no code blocks, no backticks:
{{
  "score": <0-100>,
  "grammarScore": <0-100>,
  "contextScore": <0-100>,
  "naturalnessScore": <0-100>,
  "correction": "<corrected version or 'No correction needed'>",
  "mistakes": ["<mistake 1>", "<mistake 2>"],
  "goodParts": ["<positive observation 1>", "<positive observation 2>"]
}}

CRITICAL JSON RULES:
1. Return ONLY the JSON object - no markdown, no code blocks, no backticks
2. Each array item MUST be a properly quoted JSON string
3. Inside array strings, avoid using quotes - instead of "word" should be "correction", write: word should be correction
4. Example mistakes format: ["helpfull should be helpful", "learning should be learned"]
5. All strings must be wrapped in double quotes per JSON spec"""

    def _build_response_prompt(
        self,
        user_comment: str,
        score: int,
        mistakes: List[str],
        correction: str,
        video_title: str,
        target_language: str
    ) -> str:
        """Build the roast-with-love response prompt following design doc."""
        mistakes_text = "\n".join([f"- {m}" for m in mistakes]) if mistakes else "None"

        return f"""You're someone who's fluent in {target_language} and casually drops corrections in comment sections. You're helpful but never preachy - more like a friend pointing something out than a teacher grading homework.

        Context:
        - Post: "{video_title}"
        - Their comment: "{user_comment}"
        {mistakes_text}
        {correction}

        Write a SHORT comment (1-2 sentences max) responding to their comment. If there's a mistake, mention it naturally. If they nailed it, acknowledge that. Keep it real - you're just another person scrolling and commenting.

        Response style examples:

        "*learned, but yeah same"

        "wait you actually got the subjunctive right??"

        "'helpfull' is killing me but go off"

        "that's clean actually"

        "almost perfect but it's 'era' not 'estaba' for that one"

        "bro said 'alot' 💀"

        "okay this is lowkey impressive"

        "nah that works"

        "'I learning' - my guy it's 'I learned' lol"

        "you're getting better at this fr"

        Just respond with the comment. No explanation, no quotes around it."""

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
                    r'("(?:mistakes|goodParts)":\s*\[)([^\]]+)(\])',
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
                "score": 0,
                "grammarScore": 0,
                "contextScore": 0,
                "naturalnessScore": 0,
                "correction": "Error parsing response",
                "mistakes": ["Could not parse AI response"],
                "goodParts": []
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
