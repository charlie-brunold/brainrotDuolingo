import json
import os
import re
from typing import List, Dict, Set
# Assuming Groq SDK is installed: pip install groq
try:
    from groq import Groq
except ImportError:
    # Mock classes for Groq client when SDK is not installed
    class Groq:
        def __init__(self, api_key): pass
        def chat(self): return self

    class Chat:
        def completions(self): return self

    class Completions:
        def create(self, **kwargs):
            return type('MockResponse', (object,), {
                'choices': [
                    type('MockChoice', (object,), {
                        'message': type('MockMessage', (object,), {
                            # Mock JSON list for verification response
                            'content': '[{"term": "test", "definition": "def", "category": "N", "example": "ex"}]'
                        })
                    })
                ]
            })

    # Mocking class structure correctly
    Groq.Chat = Chat
    Groq.Chat.Completions = Completions
    Groq.chat = lambda self: Groq.Chat()
    Groq.Chat.completions = lambda self: Groq.Chat.Completions()

from collections import Counter, defaultdict
import math # <-- Import math for ceiling division in batching
import time # <-- Import time for adding delays

# --- WARNING: This assumes you have a persistent file for your slang database ---
SLANG_DB_FILE = "slang_database.json"


class SlangDiscovery:
    def __init__(self, groq_api_key: str):
        # We need a client instance for the AI calls
        self.client = Groq(api_key=groq_api_key)
        self.slang_database = self.load_slang_database()
        # Basic list of common English words to filter out - EXPANDED
        self.common_words = set([
            'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you',
            'do', 'at', 'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she', 'or', 'an', 'will', 'my', 'one',
            'all', 'would', 'there', 'their', 'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me', 'when',
            'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know', 'take', 'people', 'into', 'year', 'your', 'good', 'some',
            'could', 'them', 'see', 'other', 'than', 'then', 'now', 'look', 'only', 'come', 'its', 'over', 'think', 'also',
            'back', 'after', 'use', 'two', 'how', 'our', 'work', 'first', 'well', 'way', 'even', 'new', 'want', 'because', 'any',
            'these', 'give', 'day', 'most', 'us', 'is', 'are', 'was', 'am', 'has', 'had', 'got', 'im', 'its', 'its', 'really',
            'very', 'too', 'here', 'why', 'how', 'where', 'more', 'much', 'many', 'dont', 'cant', 'isnt', 'arent', 'wasnt',
            'werent', 'didnt', 'doesnt', 'should', 'couldnt', 'wouldnt', 'shouldnt', 'thats', 'youre', 'hes', 'shes', 'im',
            'ive', 'youve', 'weve', 'theyve', 'ill', 'youll', 'hell', 'shell', 'well', 'theyll', 'video', 'comment', 'channel',
            'shorts', 'youtube', 'watch', 'watching', 'subscribe', 'thanks', 'thank', 'please', 'love', 'amazing', 'great',
            'awesome', 'nice', 'cool', 'wow', 'omg', 'lol', 'haha' # Add common comment words
        ])
        # Common bigrams to filter out
        self.common_bigrams = set([
            'it is', 'is a', 'in the', 'to be', 'on the', 'of the', 'i am', 'i was', 'he is', 'she is', 'they are', 'we are',
            'you are', 'do not', 'can not', 'will not', 'have to', 'going to', 'this is', 'that is', 'there is', 'here is',
            'so much', 'very good', 'thank you', 'you too', 'of course', 'as well', 'for real', 'no problem', 'my god', 'oh my',
            'this video', 'this short', 'i love', 'love this', 'keep it', 'it up', 'so good', 'so cool', 'looks like', 'feel like',
            'check out', 'make sure', 'first comment', 'nice video' # Add common comment phrases
        ])

    def load_slang_database(self) -> Dict:
        """
        Loads the approved slang terms from the local JSON file.
        Initializes with starter slang if the file is not found.
        """
        if os.path.exists(SLANG_DB_FILE):
            try:
                with open(SLANG_DB_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Ensure keys are lowercase for consistent lookup
                    data = {k.lower(): v for k, v in data.items()}
                    print(f"✅ Loaded {len(data)} slang terms from {SLANG_DB_FILE}")
                    return data
            except json.JSONDecodeError:
                print(f"⚠️ Corrupted database file, initializing starter slang.")
            except Exception as e:
                print(f"⚠️ Error loading database file: {e}, initializing starter slang.")


        print(f"📝 Initializing starter slang database: {SLANG_DB_FILE}")
        # Initialize with common starter slang (all lowercase keys)
        initial_db = {
            'fr': {
                'definition': 'For real - emphasizing truth or agreement',
                'category': 'agreement',
                'example': 'That was amazing fr'
            },
            'ngl': {
                'definition': 'Not gonna lie - introducing honest opinion',
                'category': 'expression',
                'example': 'Ngl this is really good'
            },
            'bussin': {
                'definition': 'Really good, especially about food',
                'category': 'positive',
                'example': 'These tacos are bussin'
            },
            'bruh': {
                'definition': 'Expression of disbelief or frustration',
                'category': 'expression',
                'example': 'Bruh what just happened'
            },
            'bet': {
                'definition': 'Agreement or confirmation, like saying okay',
                'category': 'agreement',
                'example': 'Bet, see you there'
            }
        }
        self.save_slang_database_internal(initial_db)
        return initial_db

    def save_slang_database_internal(self, data: Dict):
        """Internal method to save specific data to the file."""
        try:
            with open(SLANG_DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Failed to save slang database: {e}")


    def save_slang_database(self):
        """Saves the current slang terms to the local JSON file."""
        self.save_slang_database_internal(self.slang_database)
        # Moved print statement to verify_and_enrich for batch context
        # print(f"💾 Saved {len(self.slang_database)} terms to {SLANG_DB_FILE}")

    def get_all_slang_terms(self) -> List[str]:
        """Returns all approved slang terms for the fetcher to use."""
        return list(self.slang_database.keys())

    # --- UPDATED: STAGE 1 LOGIC WITH STRICTER LIMITS APPLIED ---
    def _extract_slang_candidates_with_context(self, all_comments: List[Dict]) -> Dict[str, List[str]]:
        """
        Analyzes comments locally to find high-frequency, unapproved words/phrases (candidates).
        Applies strict filtering and enforces MAX_CANDIDATES_TO_PROCESS limit CORRECTLY.
        Returns a dictionary of {'candidate': ['context comment 1', ...]}
        """

        candidate_counts = Counter()
        candidate_context = defaultdict(list)

        existing_slang = self.get_all_slang_terms()
        approved_slang = set(term.lower() for term in existing_slang) # Ensure lowercase set

        print(f"   Filtering against {len(approved_slang)} known phrases and {len(self.common_words)} common words.")

        for comment_data in all_comments:
            # Ensure comment_data is a dictionary and has 'text'
            if not isinstance(comment_data, dict):
                continue
            original_text = comment_data.get('text', '') # Keep original case for context
            if not original_text or len(original_text) > 250: # Skip slightly shorter comments now
                continue
            text_lower = original_text.lower()


            # Simple tokenization for words (alphanumeric only)
            words = re.findall(r'\b[a-z0-9]+\b', text_lower)

            # Check single words
            for word in words:
                # Basic check for common English words, short words, numbers
                if 2 < len(word) < 12 and not word.isdigit() and word not in approved_slang and word not in self.common_words:
                    candidate_counts[word] += 1
                    if len(candidate_context[word]) < 5: # Store up to 5 context examples
                        candidate_context[word].append(original_text) # Store original case comment

            # Check two-word phrases (bigrams)
            for i in range(len(words) - 1):
                phrase = f"{words[i]} {words[i+1]}"
                # Ensure phrase isn't just numbers and is likely phrase-like, and not common
                if (phrase not in approved_slang and
                        len(phrase.split()) == 2 and
                        not all(p.isdigit() for p in phrase.split()) and
                        phrase not in self.common_bigrams and
                        words[i] not in self.common_words and # Avoid phrases starting/ending with common words
                        words[i+1] not in self.common_words):
                    candidate_counts[phrase] += 1
                    if len(candidate_context[phrase]) < 5: # Store up to 5 context examples
                        candidate_context[phrase].append(original_text) # Store original case comment


        # Filter candidates based on frequency
        MIN_FREQUENCY = 7 # <-- INCREASED MINIMUM FREQUENCY SIGNIFICANTLY
        final_candidates = {}

        # Sort candidates by frequency (most frequent first)
        sorted_candidates = sorted(candidate_counts.items(), key=lambda item: item[1], reverse=True)

        print(f"   Raw candidate count before frequency filter: {len(sorted_candidates)}")

        # --- HARD LIMIT ON TOTAL CANDIDATES ---
        MAX_CANDIDATES_TO_PROCESS = 30 # <-- REDUCED MAX CANDIDATES PER RUN
        processed_count = 0 # Counter for how many candidates we've actually added

        for candidate, count in sorted_candidates:
             # Apply frequency filter first
             if count >= MIN_FREQUENCY:
                # Check against other filters (slang, length)
                if candidate not in approved_slang and len(candidate.split()) <= 2:
                    # Check if context list actually exists
                    if candidate in candidate_context and candidate_context[candidate]:
                        # --- APPLY MAX CANDIDATE LIMIT HERE ---
                        if processed_count < MAX_CANDIDATES_TO_PROCESS:
                            final_candidates[candidate] = candidate_context[candidate]
                            processed_count += 1
                        else:
                            # Once we hit the limit, stop processing more candidates
                            print(f"   Reached MAX_CANDIDATES_TO_PROCESS limit ({MAX_CANDIDATES_TO_PROCESS}). Stopping candidate collection.")
                            break
                    else:
                        print(f"   Skipping candidate '{candidate}' due to missing context.")


        print(f"   Filtered down to {processed_count} candidates based on frequency >= {MIN_FREQUENCY} and max count {MAX_CANDIDATES_TO_PROCESS}.")
        # Ensure the returned dictionary *actually* respects the limit
        # Although the loop should break, this is an extra safeguard
        if len(final_candidates) > MAX_CANDIDATES_TO_PROCESS:
             print(f"   Warning: Candidate dictionary size ({len(final_candidates)}) exceeds limit ({MAX_CANDIDATES_TO_PROCESS}). Trimming.")
             final_candidates = dict(list(final_candidates.items())[:MAX_CANDIDATES_TO_PROCESS])

        return final_candidates # Return the strictly limited dictionary

    # --- ORCHESTRATION METHOD (Unchanged, relies on limited input) ---
    def process_discovery_flow(self, all_comments: List[Dict]) -> List[Dict]:
        """
        Public method to orchestrate the two-stage process: Local Filtering and AI Verification in batches.
        Includes stricter filtering and delay between batches.
        """
        # 1. Local Filtering (Stage 1) - Now strictly limited
        candidates_with_context = self._extract_slang_candidates_with_context(all_comments)

        if not candidates_with_context:
            print("   No new candidates found after stricter local filtering.")
            return []

        total_candidates = len(candidates_with_context) # Should now be <= MAX_CANDIDATES_TO_PROCESS

        # 2. AI Verification and Enrichment (Stage 2) - IN BATCHES
        BATCH_SIZE = 10 # <-- REDUCED BATCH SIZE
        all_new_slang = []
        candidate_items = list(candidates_with_context.items())

        num_batches = math.ceil(total_candidates / BATCH_SIZE)

        for i in range(num_batches):
            start_index = i * BATCH_SIZE
            end_index = start_index + BATCH_SIZE
            batch_candidates = dict(candidate_items[start_index:end_index])

            print(f"\n   Processing Batch {i+1}/{num_batches} ({len(batch_candidates)} candidates)")

            # Call verify_and_enrich for the current batch
            batch_new_slang = self.verify_and_enrich_slang(batch_candidates)

            if batch_new_slang:
                all_new_slang.extend(batch_new_slang)
                # Save after each successful batch
                self.save_slang_database()
                print(f"   Batch {i+1}: Verified and saved {len(batch_new_slang)} new phrases.")
            else:
                 print(f"   Batch {i+1}: No new phrases verified by the AI.")

            # --- ADD DELAY BETWEEN BATCHES ---
            if i < num_batches - 1: # Don't sleep after the last batch
                delay_seconds = 3 # Increase delay slightly
                print(f"   Waiting {delay_seconds} seconds before next batch...")
                time.sleep(delay_seconds)


        if all_new_slang:
             print(f"\n✨ Discovery complete. Total verified phrases: {len(all_new_slang)}")
        else:
             print("\n   Discovery complete. No new phrases verified across all batches.")

        return all_new_slang

    # --- AI VERIFICATION METHOD (Unchanged, uses smaller model & reduced context) ---
    def verify_and_enrich_slang(self, batch_candidates_with_context: Dict[str, List[str]]) -> List[Dict]:
        """
        Sends a BATCH of candidates to the Groq LLM for verification using a smaller model
        and only ONE context example per candidate.
        Retrieves enriched data (definition, category, example).
        """
        if not batch_candidates_with_context:
            return []

        # Define newline character separately
        NL = chr(10)

        # 1. Format the candidates and context for the AI prompt
        MAX_CONTEXT_LENGTH = 150
        context_string = (NL + "---" + NL).join([
            # <-- REDUCED CONTEXT: Only send the FIRST example comment
            f"Candidate Term: {term}{NL}Usage Context:{NL}{comments[0][:MAX_CONTEXT_LENGTH] + ('...' if len(comments[0]) > MAX_CONTEXT_LENGTH else '') if comments else 'No context available'}"
            for term, comments in batch_candidates_with_context.items()
        ])

        system_prompt = (
            "You are a modern linguistics expert specializing in Gen Z internet culture. "
            "Your task is to review the provided list of potential terms and their usage context. "
            "For each term, determine if it is currently used as a **highly common, informal phrase, catchphrase, or internet colloquialism**. "
            "Return ONLY a single valid JSON object containing a single key 'phrases' whose value is a JSON list. "
            "The list should contain objects ONLY for the terms confirmed as popular phrases. "
            "For each confirmed term object, provide the 'term', a clear 'definition', a concise 'category' (e.g., 'Reaction', 'Slang', 'Colloquialism'), and a clean 'example' sentence of modern usage. "
            "Do not include terms that are typos, literal usages, or common English words in the list."
        )

        user_prompt = f"Review the following potential popular phrases and their usage. Return ONLY a JSON object like {{ \"phrases\": [ ... verified phrases ... ] }}: {NL}{NL}{context_string}"

        print(f"   🤖 Sending {len(batch_candidates_with_context)} candidates to Groq for verification...")

        try:
            chat_completion = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",  # <-- Using smaller, recommended model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.0 # Low temp for factual verification
            )

            ai_response_text = chat_completion.choices[0].message.content.strip()

            # 2. Parse the JSON response - Improved logic for nested lists
            response_data = json.loads(ai_response_text)
            confirmed_phrases_list = []

            if isinstance(response_data, list):
                confirmed_phrases_list = response_data # Direct list
            elif isinstance(response_data, dict):
                # Try common keys first
                if "phrases" in response_data and isinstance(response_data["phrases"], list):
                    confirmed_phrases_list = response_data["phrases"]
                elif "suggestions" in response_data and isinstance(response_data["suggestions"], list):
                    confirmed_phrases_list = response_data["suggestions"]
                elif "terms" in response_data and isinstance(response_data["terms"], list):
                     confirmed_phrases_list = response_data["terms"]
                else:
                    # Generic fallback: find the first value that is a list
                    for key, value in response_data.items():
                        if isinstance(value, list):
                            confirmed_phrases_list = value
                            print(f"   Found list under unexpected key '{key}'. Proceeding.")
                            break
                    if not confirmed_phrases_list: # If still not found
                        raise ValueError("Groq response was a dictionary, but could not find the list of phrases.")
            else:
                 raise ValueError(f"Groq response was not a JSON list or dictionary, got {type(response_data)}")


            # 3. Update the internal database (but don't save yet, save happens after batch)
            newly_added_this_batch = []
            for phrase_item in confirmed_phrases_list:
                 # Add extra validation for the structure of each item
                 if isinstance(phrase_item, dict) and 'term' in phrase_item:
                     term = phrase_item.get('term', '').lower().strip()
                     # Basic validation and check against current in-memory state
                     # Ensure term is not empty after stripping
                     if term and isinstance(term, str) and term not in self.slang_database:
                         self.slang_database[term] = {
                             'definition': phrase_item.get('definition', '').strip(),
                             'category': phrase_item.get('category', 'unknown').strip(),
                             'example': phrase_item.get('example', '').strip()
                         }
                         newly_added_this_batch.append(phrase_item) # Return the data for logging
                 else:
                     print(f"   ⚠️ Skipping malformed item in AI response: {phrase_item}")


            return newly_added_this_batch # Return only the items added in this specific batch

        except json.JSONDecodeError as json_err:
             print(f"   Groq verification failed: Could not parse JSON response.")
             if 'ai_response_text' in locals() and ai_response_text:
                 print(f"   Raw AI Response: {ai_response_text[:500]}...")
             else:
                 print("   Raw AI Response: [Empty or Undefined]")
             return [] # Return empty list on failure for this batch
        except Exception as e:
            # Check for specific rate limit error messages
            error_message = str(e).lower()
            if "rate limit" in error_message or "rate_limit_exceeded" in error_message:
                print(f"   Groq verification failed: RATE LIMIT EXCEEDED. Please wait before trying again.")
                # Optionally, re-raise or handle specific rate limit logic here
            else:
                 # Check for message length error explicitly
                 if 'reduce the length' in error_message or 'request too large' in error_message:
                     print(f"   Groq verification failed: REQUEST TOO LARGE. The prompt/context for this batch is still too long for the model.")
                 else:
                     print(f"   Groq verification failed: {e}")
            return [] # Return empty list on failure for this batch
    def get_video_details(self, video_ids: List[str]) -> List[Dict]:
        """Get detailed video information - FILTER for embeddable videos WITH comments and likely English."""
        if not video_ids:
            return []
        url = f"{self.base_url}/videos"
        # Request snippet, contentDetails, statistics, AND status parts
        params = {
            'key': self.api_key,
            'id': ','.join(video_ids),
            'part': 'snippet,contentDetails,statistics,status' # <-- ADDED 'status'
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            items = response.json().get('items', [])
            videos = []

            for item in items:
                snippet = item.get('snippet', {})
                stats = item.get('statistics', {})
                content_details = item.get('contentDetails', {})
                status = item.get('status', {}) # <-- GET status object

                # --- FILTERS ---
                # 1. Skip videos that are not embeddable
                if not status.get('embeddable', False):
                    # print(f"   Skipping video {item['id']} (embedding disabled)")
                    continue

                # 2. Skip videos with disabled comments
                comment_count_str = stats.get('commentCount')
                if comment_count_str is None: # Treat missing count as comments disabled
                    continue
                try:
                    comment_count = int(comment_count_str)
                    if comment_count < 10: # Also skip videos with very few comments
                        continue
                except ValueError:
                    continue # Skip if comment count isn't a valid number

                # 3. Filter for actual Shorts (under 61 seconds) using duration
                duration_str = content_details.get('duration')
                if not duration_str:
                    continue # Skip if duration is missing
                duration_seconds = self.parse_duration(duration_str)
                if duration_seconds <= 0 or duration_seconds > 60: # Strictly <= 60 seconds
                    continue

                # 4. Filter for likely English videos
                default_lang = snippet.get('defaultLanguage', '').lower()
                default_audio_lang = snippet.get('defaultAudioLanguage', '').lower()
                # If language is explicitly set and NOT English, skip it
                if default_lang and not default_lang.startswith('en'):
                    #print(f"   Skipping video {item['id']} (lang: {default_lang})")
                    continue
                if default_audio_lang and not default_audio_lang.startswith('en'):
                    #print(f"   Skipping video {item['id']} (audio lang: {default_audio_lang})")
                    continue
                # --- END FILTERS ---


                thumbnails = snippet.get('thumbnails', {})
                # Try getting maxres, then high, then medium, then default
                thumbnail_url = (thumbnails.get('maxres') or thumbnails.get('high') or
                                 thumbnails.get('medium') or thumbnails.get('default', {})).get('url', '')

                videos.append({
                    'video_id': item['id'],
                    'title': snippet.get('title', 'No Title'),
                    'description': snippet.get('description', ''),
                    'channel': snippet.get('channelTitle', 'Unknown Channel'),
                    'channel_id': snippet.get('channelId', ''), # Added channel ID
                    'thumbnail': thumbnail_url,
                    'duration_seconds': duration_seconds,
                    'view_count': int(stats.get('viewCount', 0)),
                    'like_count': int(stats.get('likeCount', 0)),
                    'comment_count': comment_count, # Use validated integer
                    'url': f"https://www.youtube.com/shorts/{item['id']}"
                    # No need to add embeddable status here unless frontend needs it
                })

            return videos
        except requests.exceptions.Timeout:
             print("   ⚠️ Timeout getting video details. Skipping batch.")
             return []
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error getting video details: {e}")
            return []
        except Exception as e:
             print(f"   ❌ Unexpected error getting video details: {e}")
             return []


    # --- DEPRECATED FOR TWO-STAGE FLOW, KEPT FOR BACKWARD COMPATIBILITY ---
    def discover_new_slang(self, all_comments: List[Dict], auto_approve: bool = False) -> List[Dict]:
        """Placeholder for old slang discovery, now replaced by the two-stage process."""
        print("NOTE: Using deprecated slang_discovery.discover_new_slang. This should be replaced.")
        return []

    def get_slang_info(self, term: str) -> Dict:
        """Get info about a specific slang term"""
        return self.slang_database.get(term.lower(), None)

