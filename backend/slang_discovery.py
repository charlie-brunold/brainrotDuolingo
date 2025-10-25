# slang_discovery.py

import json
import re
from typing import List, Dict, Set
from groq import Groq
from collections import Counter

class SlangDiscovery:
    """
    Automatically discovers new slang terms from YouTube comments
    and generates definitions using Groq AI
    """
    
    def __init__(self, groq_api_key: str, slang_db_file: str = "slang_database.json"):
        self.groq_client = Groq(api_key=groq_api_key)
        self.slang_db_file = slang_db_file
        self.slang_database = self.load_slang_database()
        
        # Common English words to exclude (definitely not slang)
        self.common_words = {
            'the', 'is', 'at', 'which', 'on', 'a', 'an', 'as', 'are', 'was', 'were',
            'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'can', 'to', 'of', 'in', 'for',
            'with', 'from', 'by', 'about', 'like', 'through', 'over', 'before', 'after',
            'but', 'or', 'and', 'not', 'so', 'than', 'too', 'very', 'just', 'also',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their',
            'what', 'when', 'where', 'who', 'why', 'how', 'all', 'each', 'every', 'both',
            'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'only', 'own',
            'same', 'then', 'there', 'now', 'get', 'got', 'go', 'going', 'make', 'made',
            'know', 'think', 'see', 'look', 'want', 'give', 'use', 'find', 'tell', 'ask',
            'work', 'seem', 'feel', 'try', 'leave', 'call', 'good', 'new', 'first', 'last',
            'long', 'great', 'little', 'own', 'other', 'old', 'right', 'big', 'high', 'small',
            'yeah', 'yes', 'no', 'okay', 'ok', 'thanks', 'thank', 'please', 'sorry',
            'hello', 'hi', 'hey', 'bye', 'wow', 'oh', 'ah', 'um', 'uh', 'really', 'much',
            'even', 'back', 'still', 'way', 'well', 'down', 'up', 'out', 'if', 'about'
        }
    
    def load_slang_database(self) -> Dict:
        """Load existing slang database from JSON file"""
        try:
            with open(self.slang_db_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"✅ Loaded {len(data)} slang terms from {self.slang_db_file}")
                return data
        except FileNotFoundError:
            print(f"📝 Creating new slang database: {self.slang_db_file}")
            # Initialize with common starter slang
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
        except json.JSONDecodeError:
            print(f"⚠️ Corrupted database file, creating new one")
            return {}
    
    def save_slang_database_internal(self, data: Dict):
        """Internal method to save specific data"""
        with open(self.slang_db_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def save_slang_database(self):
        """Save current slang database to JSON file"""
        self.save_slang_database_internal(self.slang_database)
        print(f"💾 Saved {len(self.slang_database)} terms to {self.slang_db_file}")
    
    def extract_potential_slang(self, comments: List[Dict], min_frequency: int = 3) -> List[str]:
        """
        Extract potential slang terms from comments based on frequency
        Returns words that appear often and aren't common English
        """
        word_counter = Counter()
        
        for comment in comments:
            text = comment.get('text', '')
            # Extract words (alphanumeric only)
            words = re.findall(r'\b\w+\b', text.lower())
            
            for word in words:
                # Filter criteria:
                # - 2-15 characters (slang is usually short)
                # - Not in common words list
                # - Not already in database
                # - Not a number
                if (2 <= len(word) <= 15 and 
                    word not in self.common_words and
                    word not in self.slang_database and
                    not word.isdigit()):
                    word_counter[word] += 1
        
        # Return top 30 most frequent words that meet minimum frequency
        potential_slang = [
            word for word, count in word_counter.most_common(30)
            if count >= min_frequency
        ]
        
        return potential_slang
    
    def is_likely_slang(self, word: str, context_examples: List[str]) -> bool:
        """
        Use Groq AI to determine if a word is likely internet/youth slang
        Returns True if it's slang, False otherwise
        """
        prompt = f"""Is "{word}" internet slang or casual youth slang used in social media comments?

Context examples where it appears:
{chr(10).join(f"- {ex[:100]}" for ex in context_examples[:5])}

Answer ONLY "YES" or "NO".
- YES if it's slang like: bussin, fr, cap, slay, vibe, lowkey, rizz, sigma, etc.
- NO if it's a normal English word, proper name, or brand name."""

        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=5
            )
            
            answer = response.choices[0].message.content.strip().upper()
            return "YES" in answer
            
        except Exception as e:
            print(f"   ⚠️ AI check failed for '{word}': {str(e)[:50]}")
            return False
    
    def generate_definition(self, word: str, context_examples: List[str]) -> Dict:
        """
        Use Groq AI to generate definition, category, and example for a slang term
        """
        prompt = f"""Analyze the slang term "{word}" from these YouTube comments:

{chr(10).join(f"- {ex[:120]}" for ex in context_examples[:6])}

Provide:
1. Definition (max 12 words, simple and clear)
2. Category: MUST be exactly one of: positive, negative, agreement, descriptive, expression
3. Example sentence (short and natural)

Format EXACTLY like this (don't add extra text):
DEFINITION: [your definition]
CATEGORY: [one category from above list]
EXAMPLE: [example sentence]"""

        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=120
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse response
            definition = ""
            category = "descriptive"
            example = ""
            
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('DEFINITION:'):
                    definition = line.replace('DEFINITION:', '').strip()
                elif line.startswith('CATEGORY:'):
                    cat = line.replace('CATEGORY:', '').strip().lower()
                    if cat in ['positive', 'negative', 'agreement', 'descriptive', 'expression']:
                        category = cat
                elif line.startswith('EXAMPLE:'):
                    example = line.replace('EXAMPLE:', '').strip()
            
            # Fallback if parsing failed
            if not definition:
                definition = f"Popular slang term used in casual conversation"
            if not example:
                example = f"That's so {word}"
            
            return {
                'definition': definition,
                'category': category,
                'example': example,
                'discovered_from': context_examples[:2]
            }
            
        except Exception as e:
            print(f"   ⚠️ Definition generation failed for '{word}': {str(e)[:50]}")
            return {
                'definition': f"Popular slang term used in social media",
                'category': 'descriptive',
                'example': f"Example with {word}",
                'discovered_from': context_examples[:2]
            }
    
    def discover_new_slang(self, comments: List[Dict], auto_approve: bool = False) -> List[Dict]:
        """
        Main function: Discover new slang from comments
        
        Args:
            comments: List of comment dicts with 'text' field
            auto_approve: If True, automatically add to database
        
        Returns:
            List of newly discovered slang terms with definitions
        """
        if not comments:
            print("⚠️ No comments to analyze")
            return []
        
        print(f"\n🔍 Analyzing {len(comments)} comments for new slang...")
        
        # Step 1: Extract potential slang terms
        potential_slang = self.extract_potential_slang(comments, min_frequency=3)
        
        if not potential_slang:
            print("   No new potential slang found")
            return []
        
        print(f"   Found {len(potential_slang)} potential terms: {potential_slang[:10]}")
        
        new_slang_terms = []
        
        # Limit to top 10 to avoid excessive API calls
        for word in potential_slang[:10]:
            # Get context examples
            examples = [
                c['text'] for c in comments 
                if re.search(r'\b' + re.escape(word) + r'\b', c['text'].lower())
            ][:8]
            
            # Step 2: Verify it's actually slang using AI
            print(f"   🤔 Checking: '{word}'...", end=" ")
            
            if self.is_likely_slang(word, examples):
                print("✅ IS SLANG")
                
                # Step 3: Generate definition
                slang_info = self.generate_definition(word, examples)
                slang_info['term'] = word
                
                if auto_approve:
                    # Add to database
                    self.slang_database[word] = slang_info
                    print(f"      📝 Added: {slang_info['definition']}")
                
                new_slang_terms.append(slang_info)
            else:
                print("❌ not slang")
        
        if auto_approve and new_slang_terms:
            self.save_slang_database()
            print(f"\n✨ Discovered and saved {len(new_slang_terms)} new slang terms!")
        
        return new_slang_terms
    
    def get_all_slang_terms(self) -> Set[str]:
        """Get set of all known slang terms"""
        return set(self.slang_database.keys())
    
    def get_slang_info(self, term: str) -> Dict:
        """Get info about a specific slang term"""
        return self.slang_database.get(term.lower(), None)

