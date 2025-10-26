import React, { useState, useRef, useEffect } from 'react'; 
import { Heart, MessageCircle, Share2, Bookmark, ChevronUp, ChevronDown, Send, Sparkles, Lightbulb, X, Check, Plus } from 'lucide-react';
import MySlang from './Myslang.jsx';

// --- SLANG TERMS (Static Data) ---
const SLANG_TERMS = {
  'cook': { definition: 'To do something very well, to excel', example: 'He really cooked with that comment' },
  'cooked': { definition: 'Ruined, done for, or extremely tired', example: 'Bro is cooked after that fail' },
  'sigma': { definition: 'An independent, self-reliant person; a leader', example: 'That was such a sigma move' },
  'rizz': { definition: 'Charisma, especially in romantic contexts', example: 'He has infinite rizz' },
  'gyat': { definition: 'Expression of excitement or surprise', example: 'Gyat! That was unexpected' },
  'skibidi': { definition: 'Nonsense term used for emphasis or humor', example: 'That\'s so skibidi' },
  'ohio': { definition: 'Strange, weird, or cursed', example: 'This video is so Ohio' },
  'mewing': { definition: 'Tongue posture technique (often used ironically)', example: 'Can\'t talk, I\'m mewing' },
  'mogging': { definition: 'Looking better than someone else', example: 'He\'s mogging everyone here' },
  'aura': { definition: 'Points representing someone\'s vibe or presence', example: '+1000 aura for that' },
  'glazing': { definition: 'Excessively praising or hyping someone', example: 'Stop glazing him bro' },
  'edging': { definition: 'Being on the edge or border of something', example: 'This video is edging perfection' },
  'bussin': { definition: 'Really good, excellent', example: 'This content is bussin fr' },
  'no cap': { definition: 'No lie, for real', example: 'That was fire no cap' },
  'fr': { definition: 'For real, seriously', example: 'This is peak content fr' },
  'slay': { definition: 'To do something exceptionally well', example: 'You totally slayed that comment' },
  'ate': { definition: 'Did something perfectly', example: 'She ate and left no crumbs' },
  'lowkey': { definition: 'Somewhat, kind of, secretly', example: 'This is lowkey fire' },
  'highkey': { definition: 'Very, obviously, definitely', example: 'This is highkey the best video' },
  'mid': { definition: 'Mediocre, not good or bad', example: 'That take was mid' },
  'based': { definition: 'Being yourself regardless of others\' opinions', example: 'That\'s a based opinion' },
  'ratio': { definition: 'When a reply gets more likes than the original', example: 'Ratio + L + fell off' },
  'L': { definition: 'Loss, failure, or something bad', example: 'That\'s an L take' },
  'W': { definition: 'Win, success, or something good', example: 'This is a W video' },
};

export default function BrainrotTikTok({ shortsData }) {
  const COMMON_WORDS = new Set([
    // Articles & pronouns
    'a', 'an', 'the', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'their', 'our', 'mine', 'yours', 'hers', 'ours', 'theirs',
  
    // Basic verbs
    'be', 'am', 'is', 'are', 'was', 'were', 'been', 'being', 
    'have', 'has', 'had', 'do', 'does', 'did', 'go', 'goes', 'went', 'gone', 
    'get', 'gets', 'got', 'make', 'makes', 'made', 'see', 'saw', 'seen',
    'come', 'came', 'know', 'knew', 'known', 'think', 'thought', 
    'say', 'says', 'said', 'want', 'like', 'need', 'can', 'could', 'will', 'would', 'shall', 'should', 'may', 'might', 'must',
  
    // Common nouns
    'man', 'woman', 'boy', 'girl', 'people', 'time', 'day', 'year', 'thing', 'person', 'world', 'school', 'place', 'home', 'life', 'hand', 'eye', 'work', 'week', 'way', 'child', 'friend', 'family',
  
    // Common adjectives
    'good', 'bad', 'new', 'old', 'first', 'last', 'long', 'short', 'big', 'small', 'great', 'little', 'other', 'same', 'different', 'young', 'right', 'left', 'happy', 'sad', 'easy', 'hard',
  
    // Prepositions
    'in', 'on', 'at', 'by', 'with', 'from', 'to', 'for', 'of', 'about', 'over', 'under', 'between', 'into', 'through', 'before', 'after', 'around', 'against', 'without', 'the', 'that', 'this',
  
    // Conjunctions
    'and', 'or', 'but', 'because', 'so', 'if', 'when', 'while', 'than', 'though', 'although', 'as',
  
    // Common adverbs
    'very', 'really', 'just', 'now', 'then', 'there', 'here', 'always', 'never', 'sometimes', 'often', 'again', 'too', 'enough',
  
    // Numbers
    'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'hundred', 'thousand',
  
    // Miscellaneous
    'yes', 'no', 'not', 'ok', 'okay', 'hello', 'hi', 'bye', 'thanks', 'thank', 'please'
  ]);
  
  const [currentVideoIndex, setCurrentVideoIndex] = useState(0);
  const [showComments, setShowComments] = useState(false);
  const [comment, setComment] = useState('');
  const [userComments, setUserComments] = useState([]);
  const [suggestedSlang, setSuggestedSlang] = useState([]);
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [touchStart, setTouchStart] = useState(0);
  const [touchEnd, setTouchEnd] = useState(0);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [explanations, setExplanations] = useState({});
  const [activeExplanation, setActiveExplanation] = useState(null);
  const [loadingExplanation, setLoadingExplanation] = useState(null);
  const [mySlang, setMySlang] = useState(() => {
    const saved = sessionStorage.getItem('brainrot_my_slang');
    return saved ? JSON.parse(saved) : [];
  });
  const [showMySlang, setShowMySlang] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [isVideoReady, setIsVideoReady] = useState(false);
  const containerRef = useRef(null);
  
  const VIDEOS = shortsData || [];
  const currentVideo = VIDEOS[currentVideoIndex];
  const videoId = currentVideo?.url ? currentVideo.url.match(/(?:v=|\/shorts\/)([a-zA-Z0-9_-]{11})/) ? currentVideo.url.match(/(?:v=|\/shorts\/)([a-zA-Z0-9_-]{11})/)[1] : null : null;

  const [hoveredWord, setHoveredWord] = useState(null);
  const [tooltipLocked, setTooltipLocked] = useState(false);
  const [wordPosition, setWordPosition] = useState({ x: 0, y: 0 });
  const [loadingDefinition, setLoadingDefinition] = useState(false);
  const [definitionCache, setDefinitionCache] = useState({});
  const [hoverTimeoutId, setHoverTimeoutId] = useState(null);
  const [knownWords, setKnownWords] = useState(() => {
    const saved = sessionStorage.getItem('brainrot_known_words');
    return saved ? JSON.parse(saved) : [];
  });

  useEffect(() => {
    if (currentVideoIndex === 0 && !isVideoReady) {
      const timer = setTimeout(() => {
        setIsVideoReady(true);
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [currentVideoIndex, isVideoReady]);

  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num?.toString() || '0';
  };

  const scrollToVideo = (index) => {
    if (index >= 0 && index < VIDEOS.length) {
      setCurrentVideoIndex(index);
      setShowComments(false);
      setUserComments([]);
      setComment('');
      setShowFeedback(false);
    }
  };

  const handleWheel = (e) => {
    if (showComments) {
        return;
    } 

    if (e.deltaY > 0) {
      scrollToVideo(currentVideoIndex + 1);
    } else {
      scrollToVideo(currentVideoIndex - 1);
    }
  };

  const handleTouchStart = (e) => {
    if (showComments) return;
    setTouchStart(e.targetTouches[0].clientY);
  };

  const handleTouchMove = (e) => {
    if (showComments) return;
    setTouchEnd(e.targetTouches[0].clientY);
  };

  const handleTouchEnd = () => {
    if (showComments) return;
    const SWIPE_THRESHOLD = 50;

    if (touchStart - touchEnd > SWIPE_THRESHOLD) {
      scrollToVideo(currentVideoIndex + 1);
    }

    if (touchStart - touchEnd < -SWIPE_THRESHOLD) {
      scrollToVideo(currentVideoIndex - 1);
    }
    
    setTouchStart(0);
    setTouchEnd(0);
  };

  useEffect(() => {
    if (currentVideo && currentVideo.unique_slang_terms) {
      const suggestions = currentVideo.unique_slang_terms.slice(0, 3);
      setSuggestedSlang(suggestions);
    }
  }, [currentVideoIndex, currentVideo]);

  const addSlangToComment = (slang) => {
    setComment(prev => prev + (prev ? ' ' : '') + slang + ' ');
  };

  const evaluateCommentWithAI = async (commentText) => {
    try {
      const response = await fetch('http://localhost:3001/api/evaluate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          videoTitle: currentVideo.title || 'Untitled Video',
          videoDescription: currentVideo.description || '',
          userComment: commentText,
          targetLanguage: 'English',
          videoLikeCount: currentVideo.like_count || 0,
          availableSlang: currentVideo.unique_slang_terms || [],
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to evaluate comment');
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error evaluating comment:', error);
      throw error;
    }
  };

  const generateAIResponse = async (commentText, evaluation) => {
    try {
      const response = await fetch('http://localhost:3001/api/respond', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userComment: commentText,
          score: evaluation.score,
          mistakes: evaluation.mistakes || [],
          correction: evaluation.correction || '',
          videoTitle: currentVideo.title || 'Untitled Video',
          targetLanguage: 'English',
          availableSlang: currentVideo.unique_slang_terms || [],
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate AI response');
      }

      const data = await response.json();
      return data.responses;
    } catch (error) {
      console.error('Error generating AI response:', error);
      throw error;
    }
  };

  const fetchCommentExplanation = async (commentId, commentText, detectedSlang) => {
    try {
      const response = await fetch('http://localhost:3001/api/explain-comment', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          commentText: commentText,
          videoTitle: currentVideo.title || 'Untitled Video',
          videoDescription: currentVideo.description || '',
          detectedSlang: detectedSlang || [],
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch explanation');
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error fetching explanation:', error);
      throw error;
    }
  };

  const handleExplainClick = async (commentId, commentText, detectedSlang) => {
    if (activeExplanation === commentId) {
      setActiveExplanation(null);
      return;
    }

    if (explanations[commentId]) {
      setActiveExplanation(commentId);
      return;
    }

    setLoadingExplanation(commentId);
    try {
      const explanation = await fetchCommentExplanation(commentId, commentText, detectedSlang);

      setExplanations(prev => ({
        ...prev,
        [commentId]: explanation
      }));

      setActiveExplanation(commentId);

      if (explanation.slangBreakdown && explanation.slangBreakdown.length > 0) {
        const newSlangTerms = explanation.slangBreakdown.map(slang => ({
          term: slang.term,
          definition: slang.definition,
          example: slang.usage,
          learnedAt: Date.now(),
          videoTitle: currentVideo.title,
          videoId: currentVideo.video_id
        }));

        setMySlang(prev => {
          const existingTerms = new Set(prev.map(s => s.term.toLowerCase()));
          const uniqueNewTerms = newSlangTerms.filter(
            slang => !existingTerms.has(slang.term.toLowerCase())
          );

          const updated = [...prev, ...uniqueNewTerms];
          sessionStorage.setItem('brainrot_my_slang', JSON.stringify(updated));
          return updated;
        });
      }
    } catch (error) {
      console.error('Failed to get explanation:', error);
      setExplanations(prev => ({
        ...prev,
        [commentId]: {
          translation: 'Could not load explanation. Please try again.',
          slangBreakdown: []
        }
      }));
      setActiveExplanation(commentId);
    } finally {
      setLoadingExplanation(null);
    }
  };

  const fetchSuggestions = async () => {
    if (mySlang.length === 0) {
      setSuggestions([]);
      return;
    }

    setLoadingSuggestions(true);
    try {
      const response = await fetch('http://localhost:3001/api/suggest-slang', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          learnedTerms: mySlang.map(s => s.term)
        })
      });

      if (!response.ok) {
        throw new Error('Failed to fetch suggestions');
      }

      const data = await response.json();

      const learnedTermsLower = new Set(mySlang.map(s => s.term.toLowerCase()));
      const seenSuggestions = new Set();
      const filteredSuggestions = (data.suggestions || []).filter(suggestion => {
        const termLower = suggestion.term.toLowerCase();
        if (learnedTermsLower.has(termLower) || seenSuggestions.has(termLower)) {
          return false;
        }
        seenSuggestions.add(termLower);
        return true;
      });

      setSuggestions(filteredSuggestions);
    } catch (error) {
      console.error('Error fetching suggestions:', error);
      setSuggestions([]);
    } finally {
      setLoadingSuggestions(false);
    }
  };

  const tokenizeText = (text) => {
    if (!text) return [];
    
    const words = text.split(/(\s+)/);
    const tokens = [];
    
    for (let i = 0; i < words.length; i++) {
      const word = words[i];
      const cleanWord = word.toLowerCase().replace(/[^a-z0-9\s]/g, '');
      
      // Skip whitespace and very short words
      if (!cleanWord || cleanWord.length < 2) {
        tokens.push({
          text: word,
          isWord: false
        });
        continue;
      }
      
      // Skip common words - don't make them hoverable
      if (COMMON_WORDS.has(cleanWord)) {
        tokens.push({
          text: word,
          isWord: false
        });
        continue;
      }
      
      const isKnown = knownWords.includes(cleanWord);
      const isLearned = mySlang.some(s => s.term.toLowerCase() === cleanWord);
      
      tokens.push({
        text: word,
        isWord: true,
        cleanWord: cleanWord,
        isKnown: isKnown,
        isLearned: isLearned
      });
    }
    
    return tokens;
  };

  // Update handleWordHover function
// Update handleWordHover to be more reliable
const handleWordHover = async (cleanWord, event) => {
  event.stopPropagation();
  
  // Clear any existing timeout
  if (hoverTimeoutId) {
    clearTimeout(hoverTimeoutId);
    setHoverTimeoutId(null);
  }

  // If tooltip is locked, don't override - but allow same word to refresh
  if (tooltipLocked && hoveredWord && hoveredWord.word !== cleanWord) {
    return;
  }
  
  const rect = event.target.getBoundingClientRect();
  setWordPosition({
    x: rect.left + rect.width / 2,
    y: rect.top - 10
  });

  // Check cache first before showing loading state
  if (definitionCache[cleanWord]) {
    setHoveredWord(definitionCache[cleanWord]);
    setLoadingDefinition(false);
    return;
  }

  // Show loading state for new words
  setLoadingDefinition(true);
  setHoveredWord({ word: cleanWord, definition: 'Loading...', example: '' });

  try {
    const definition = await fetchWordDefinition(cleanWord);
    setHoveredWord(definition);
  } catch (error) {
    console.error('Error in handleWordHover:', error);
    setHoveredWord({
      word: cleanWord,
      definition: 'Failed to load definition',
      example: ''
    });
  } finally {
    setLoadingDefinition(false);
  }
};

// Update handleWordLeave to use a ref for checking lock state
const handleWordLeave = () => {
  // Don't close if tooltip is locked (user is interacting with it)
  if (tooltipLocked) return;
  
  // Clear any existing timeout first
  if (hoverTimeoutId) {
    clearTimeout(hoverTimeoutId);
  }
  
  // Set a short delay before closing to allow moving to tooltip
  const timeoutId = setTimeout(() => {
    // Double-check lock state hasn't changed during timeout
    setTooltipLocked((currentLocked) => {
      if (!currentLocked) {
        setHoveredWord(null);
      }
      return currentLocked;
    });
  }, 150);
  
  setHoverTimeoutId(timeoutId);
};

// Update fetchWordDefinition to not change loading state (we handle it in handleWordHover)
const fetchWordDefinition = async (word) => {
  // Check cache first
  if (definitionCache[word]) {
    return definitionCache[word];
  }

  try {
    const response = await fetch('http://localhost:3001/api/define-word', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        word: word,
        context: currentVideo.title || ''
      })
    });

    if (!response.ok) {
      throw new Error('Failed to fetch definition');
    }

    const data = await response.json();
    
    // Cache the result
    setDefinitionCache(prev => ({
      ...prev,
      [word]: data
    }));

    return data;
  } catch (error) {
    console.error('Error fetching definition:', error);
    return {
      word: word,
      definition: 'Definition not available',
      example: ''
    };
  }
};

// Update handleWantToLearn and handleAlreadyKnow to properly reset state
const handleWantToLearn = (term, definition, example) => {
  const newSlangTerm = {
    term: term,
    definition: definition,
    example: example,
    learnedAt: Date.now(),
    videoTitle: currentVideo.title,
    videoId: currentVideo.video_id
  };

  setMySlang(prev => {
    const existingTerms = new Set(prev.map(s => s.term.toLowerCase()));
    if (existingTerms.has(term.toLowerCase())) {
      return prev;
    }
    const updated = [...prev, newSlangTerm];
    sessionStorage.setItem('brainrot_my_slang', JSON.stringify(updated));
    return updated;
  });

  // Reset all tooltip state
  setHoveredWord(null);
  setTooltipLocked(false);
  if (hoverTimeoutId) {
    clearTimeout(hoverTimeoutId);
    setHoverTimeoutId(null);
  }
};

const handleAlreadyKnow = (term) => {
  setKnownWords(prev => {
    if (prev.includes(term)) return prev;
    const updated = [...prev, term];
    sessionStorage.setItem('brainrot_known_words', JSON.stringify(updated));
    return updated;
  });

  // Reset all tooltip state
  setHoveredWord(null);
  setTooltipLocked(false);
  if (hoverTimeoutId) {
    clearTimeout(hoverTimeoutId);
    setHoverTimeoutId(null);
  }
};

  useEffect(() => {
    if (showMySlang && mySlang.length > 0) {
      fetchSuggestions();
    }
  }, [showMySlang]);

  const handleSubmitComment = async () => {
    if (!comment.trim() || isEvaluating) return;

    setIsEvaluating(true);

    try {
      const evaluation = await evaluateCommentWithAI(comment);
      const aiResponses = await generateAIResponse(comment, evaluation);

      const newComment = {
        id: Date.now(),
        text: comment,
        user: 'You',
        likes: evaluation.likes,
        evaluation,
        aiResponses: aiResponses
      };

      setUserComments(prev => [newComment, ...prev]);

      setFeedback({
        score: evaluation.score,
        grammarScore: evaluation.grammarScore,
        contextScore: evaluation.contextScore,
        naturalnessScore: evaluation.naturalnessScore,
        correction: evaluation.correction,
        mistakes: evaluation.mistakes,
        goodParts: evaluation.goodParts,
        message: evaluation.score >= 80
          ? "You're cooking! 🔥"
          : evaluation.score >= 50
          ? "Not bad, keep practicing!"
          : "Keep learning!"
      });

      setShowFeedback(true);
      setComment('');
      setTimeout(() => setShowFeedback(false), 8000);
    } catch (error) {
      console.error('Error submitting comment:', error);

      setFeedback({
        score: 0,
        message: "Oops! Couldn't evaluate your comment. Check if the backend is running.",
        mistakes: [],
        goodParts: [],
        correction: comment
      });
      setShowFeedback(true);
      setTimeout(() => setShowFeedback(false), 5000);
    } finally {
      setIsEvaluating(false);
    }
  };

  if (!currentVideo) {
    return (
      <div className="h-screen w-full bg-black flex items-center justify-center">
        <div className="text-white text-center">
          <div className="text-4xl mb-4">📭</div>
          <div className="text-xl">No videos available</div>
          <div className="text-sm text-gray-400 mt-2">Load some shorts data to get started</div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-full bg-black relative overflow-hidden flex flex-col">
      <div className="flex-shrink-0 flex justify-center gap-8 p-4 bg-black z-50 border-b border-gray-800">
        <button
          onClick={() => setShowMySlang(true)}
          className={`text-sm font-semibold transition-colors pb-1 ${
            showMySlang
              ? 'text-white border-b-2 border-white'
              : 'text-white/70 hover:text-white'
          }`}
        >
          My Words {mySlang.length > 0 && `(${mySlang.length})`}
        </button>
        <button
          onClick={() => setShowMySlang(false)}
          className={`text-sm font-semibold transition-colors pb-1 ${
            !showMySlang
              ? 'text-white border-b-2 border-white'
              : 'text-white/70 hover:text-white'
          }`}
        >
          For You
        </button>
      </div>

      <div className="flex-1 relative overflow-hidden">
        {!showMySlang ? (
          <>
            <div
              ref={containerRef}
              onWheel={handleWheel}
              onTouchStart={handleTouchStart}
              onTouchMove={handleTouchMove}
              onTouchEnd={handleTouchEnd}
              className="absolute inset-0"
            >
              {VIDEOS.map((video, index) => {
                const videoIdForIndex = video?.url ? video.url.match(/(?:v=|\/shorts\/)([a-zA-Z0-9_-]{11})/) ? video.url.match(/(?:v=|\/shorts\/)([a-zA-Z0-9_-]{11})/)[1] : null : null;
                const isCurrentVideo = index === currentVideoIndex;

                return (
                  <div
                    key={`video-${index}-${videoIdForIndex}`}
                    className="absolute inset-0 w-full h-full flex items-center justify-center bg-black transition-opacity duration-500"
                    style={{
                      opacity: isCurrentVideo ? 1 : 0,
                      pointerEvents: isCurrentVideo ? 'auto' : 'none',
                      zIndex: isCurrentVideo ? 1 : 0
                    }}
                  >
                    {videoIdForIndex && isCurrentVideo ? (
                      <iframe
                        key={`iframe-${videoIdForIndex}-${currentVideoIndex}`}
                        width="100%"
                        height="100%"
                        src={`https://www.youtube.com/embed/${videoIdForIndex}?autoplay=1&mute=1&controls=1&rel=0&modestbranding=1&playsinline=1`}
                        title={video.title}
                        frameBorder="0"
                        allow="autoplay; accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                        allowFullScreen
                        className="absolute inset-0"
                        style={{ objectFit: 'cover' }}
                      />
                    ) : videoIdForIndex ? (
                      <div className="w-full h-full bg-black" />
                    ) : (
                      <div className="text-center text-white p-8">
                        <img
                          src={video.thumbnail}
                          alt={video.title}
                          className="max-w-full max-h-full rounded-lg mb-4"
                        />
                        <div className="text-2xl font-bold mb-2">{video.title}</div>
                        <div className="text-lg opacity-80">@{video.channel}</div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>   

            <div className="absolute inset-0 pointer-events-none">
              <div className="h-full w-full relative pointer-events-auto" style={{ pointerEvents: 'none' }}>
                <div className="h-full w-full flex items-center justify-center bg-transparent" style={{ pointerEvents: 'none' }}>
                </div>

                {!showComments && (
                  <div className="absolute left-4 top-1/2 transform -translate-y-1/2 flex flex-col gap-4 z-50 transition-opacity duration-300" style={{ pointerEvents: 'auto' }}>
                    <button
                      onClick={() => scrollToVideo(currentVideoIndex - 1)}
                      disabled={currentVideoIndex === 0}
                      className="p-3 bg-white/20 backdrop-blur-sm rounded-full disabled:opacity-30 hover:bg-white/30 transition-colors"
                    >
                      <ChevronUp className="w-6 h-6 text-white" />
                    </button>
                    <button
                      onClick={() => scrollToVideo(currentVideoIndex + 1)}
                      disabled={currentVideoIndex === VIDEOS.length - 1}
                      className="p-3 bg-white/20 backdrop-blur-sm rounded-full disabled:opacity-30 hover:bg-white/30 transition-colors"
                    >
                      <ChevronDown className="w-6 h-6 text-white" />
                    </button>
                  </div>
                )}

                <div className="absolute right-4 bottom-24 flex flex-col gap-6 items-center z-10" style={{ pointerEvents: 'auto' }}>
                  <div className="flex flex-col items-center gap-1">
                    <div className="p-3 bg-white/20 backdrop-blur-sm rounded-full">
                      <Heart className="w-7 h-7 text-white" />
                    </div>
                    <span className="text-white text-xs font-semibold">{formatNumber(currentVideo.like_count)}</span>
                  </div>
                  <div className="flex flex-col items-center gap-1">
                    <button
                      onClick={() => setShowComments(!showComments)}
                      className="p-3 bg-white/20 backdrop-blur-sm rounded-full"
                    >
                      <MessageCircle className="w-7 h-7 text-white" />
                    </button>
                    <span className="text-white text-xs font-semibold">{formatNumber(currentVideo.comment_count)}</span>
                  </div>
                  <div className="p-3 bg-white/20 backdrop-blur-sm rounded-full">
                    <Share2 className="w-7 h-7 text-white" />
                  </div>
                  <div className="p-3 bg-white/20 backdrop-blur-sm rounded-full">
                    <Bookmark className="w-7 h-7 text-white" />
                  </div>
                </div>

                <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/80 to-transparent z-10" style={{ pointerEvents: 'auto' }}>
                  <div className="text-white">
                    <div className="font-bold">@{currentVideo.channel}</div>
                    <div className="text-sm mt-1">{currentVideo.title}</div>
                    {currentVideo.unique_slang_terms && currentVideo.unique_slang_terms.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {currentVideo.unique_slang_terms.map((slang, idx) => (
                          <span key={idx} className="text-xs bg-white/20 px-2 py-1 rounded-full">
                            #{slang}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {showComments && (
                  <div 
                    className="absolute inset-0 bg-black/50 z-30"
                    onClick={() => setShowComments(false)}
                    style={{ pointerEvents: 'auto' }}
                  >
                    <div 
                      className="absolute bottom-0 left-0 right-0 h-2/3 bg-gray-900 rounded-t-3xl flex flex-col"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <div className="p-4 border-b border-gray-700">
                        <div 
                          className="w-12 h-1 bg-gray-600 rounded-full mx-auto mb-4 cursor-pointer"
                          onClick={() => setShowComments(false)}
                        ></div>
                        
                      </div>

                      {showFeedback && feedback && (
                        <div className="sticky top-0 z-10 p-4 bg-blue-600 border-b border-gray-700">
                          <div className="flex items-start gap-3">
                            <div className="text-3xl">
                              {feedback.score >= 80 ? '🔥' : feedback.score >= 50 ? '👍' : '📚'}
                            </div>
                            <div className="flex-1">
                              <div className="text-white font-bold mb-1">{feedback.message}</div>
                              <div className="text-white/90 text-sm mb-2">
                                Overall Score: {Math.round(feedback.score)}%
                              </div>
                              {feedback.grammarScore !== undefined && (
                                <div className="text-white/80 text-xs mb-2 flex gap-3">
                                  <span>Grammar: {feedback.grammarScore}%</span>
                                  <span>Context: {feedback.contextScore}%</span>
                                  <span>Natural: {feedback.naturalnessScore}%</span>
                                </div>
                              )}
                              {feedback.correction && feedback.correction !== comment && (
                                <div className="text-green-300 text-xs mb-1">
                                  ✓ Corrected: {feedback.correction}
                                </div>
                              )}
                              {feedback.goodParts && feedback.goodParts.length > 0 && (
                                <div className="text-green-300 text-xs mb-1">
                                  ✓ Good: {feedback.goodParts.join(', ')}
                                </div>
                              )}
                              {feedback.mistakes && feedback.mistakes.length > 0 && (
                                <div className="text-red-300 text-xs mb-1">
                                  ✗ Tips: {feedback.mistakes.join(', ')}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      )}

                      <div className="flex-1 overflow-y-auto p-4 space-y-4">
                        {currentVideo.top_comments && currentVideo.top_comments.slice(0, 10).map((c, idx) => {
                          const commentId = c.comment_id;
                          const tokens = tokenizeText(c.text);
                          const hasExplanation = explanations[commentId];
                          const isExplanationActive = activeExplanation === commentId;
                          const isLoadingExplanation = loadingExplanation === commentId;

                          return (
                            <div key={commentId} className="relative">
                              <div className="flex gap-3">
                                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-green-500 to-teal-500 flex-shrink-0"></div>
                                <div className="flex-1">
                                  <div className="flex items-center gap-2">
                                    <div className="text-white font-semibold text-sm">{c.author}</div>
                                  </div>
                                  <div className="text-white/90 text-sm mt-1 leading-relaxed">
                                    {tokens.map((token, i) => {
                                      if (!token.isWord) {
                                        return <span key={i}>{token.text}</span>;
                                      }

                                      // Only make words hoverable if explanation has been loaded
                                      if (!hasExplanation) {
                                        return <span key={i}>{token.text}</span>;
                                      }

                                      let className = "cursor-pointer transition-colors border-b border-dotted ";
                                      if (token.isLearned) {
                                        className += "text-green-400 border-green-400";
                                      } else if (token.isKnown) {
                                        className += "text-gray-400 border-gray-600";
                                      } else {
                                        className += "text-white border-white/30 hover:border-white hover:text-blue-300";
                                      }

                                      return (
                                        <span
                                          key={i}
                                          className={className}
                                          onMouseEnter={(e) => handleWordHover(token.cleanWord, e)}
                                          onMouseLeave={handleWordLeave}
                                        >
                                          {token.text}
                                        </span>
                                      );
                                    })}
                                  </div>
                                  <div className="flex gap-4 mt-2">
                                    <button className="text-gray-400 text-xs flex items-center gap-1">
                                      <Heart className="w-3 h-3" /> {c.like_count}
                                    </button>
                                    <button
                                      onClick={() => handleExplainClick(commentId, c.text, c.detected_slang || [])}
                                      disabled={isLoadingExplanation}
                                      className={`text-xs flex items-center gap-1 transition-colors ${
                                        isExplanationActive
                                          ? 'text-yellow-400'
                                          : 'text-gray-400 hover:text-yellow-300'
                                      }`}
                                    >
                                      {isLoadingExplanation ? (
                                        <div className="w-3 h-3 border border-gray-400 border-t-transparent rounded-full animate-spin" />
                                      ) : (
                                        <Lightbulb className="w-3 h-3" />
                                      )}
                                      {isLoadingExplanation ? 'Loading...' : 'Explain'}
                                    </button>
                                  </div>
                                </div>
                              </div>

                              {/* Explanation UI */}
                              {isExplanationActive && hasExplanation && (
                                <div className="mt-3 ml-11 bg-gradient-to-br from-blue-900/40 to-purple-900/40 rounded-lg p-4 border border-blue-500/30">
                                  <div className="flex items-start justify-between mb-3">
                                    <div className="text-blue-300 font-semibold text-xs flex items-center gap-1">
                                      <Lightbulb className="w-4 h-4" />
                                      Simplified Translation
                                    </div>
                                    <button
                                      onClick={() => setActiveExplanation(null)}
                                      className="text-gray-400 hover:text-white transition-colors"
                                    >
                                      <X className="w-4 h-4" />
                                    </button>
                                  </div>

                                  <div className="text-white/90 text-sm mb-3 leading-relaxed">
                                    {hasExplanation.translation}
                                  </div>

                                  {hasExplanation.slangBreakdown && hasExplanation.slangBreakdown.length > 0 && (
                                    <div className="space-y-2 border-t border-blue-500/20 pt-3">
                                      <div className="text-purple-300 font-semibold text-xs mb-2">Slang Breakdown:</div>
                                      {hasExplanation.slangBreakdown.map((slang, idx) => (
                                        <div key={idx} className="bg-black/20 rounded p-2">
                                          <div className="text-yellow-300 font-bold text-xs">{slang.term}</div>
                                          <div className="text-white/80 text-xs mt-1">{slang.definition}</div>
                                          <div className="text-gray-400 italic text-xs mt-1">"{slang.usage}"</div>
                                        </div>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          );
                        })}

                        {hoveredWord && (
                          <div
                            className="fixed z-[100]"
                            style={{
                              left: `${wordPosition.x}px`,
                              top: `${wordPosition.y}px`,
                              transform: 'translate(-50%, -100%)',
                              pointerEvents: 'auto'
                            }}
                            onMouseEnter={(e) => {
                              e.stopPropagation();
                              // Clear any pending timeout when entering tooltip
                              if (hoverTimeoutId) {
                                clearTimeout(hoverTimeoutId);
                                setHoverTimeoutId(null);
                              }
                              setTooltipLocked(true);
                            }}
                            onMouseLeave={(e) => {
                              e.stopPropagation();
                              setTooltipLocked(false);
                              // Immediately close when leaving tooltip
                              setHoveredWord(null);
                            }}
                          >
                            <div 
                              className="bg-gray-900 border-2 border-blue-400 rounded-lg shadow-2xl p-4 mb-2"
                              style={{ minWidth: '250px', maxWidth: '350px' }}
                            >
                              {loadingDefinition ? (
                                <div className="text-white text-center py-4">
                                  <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                                  Loading...
                                </div>
                              ) : (
                                <>
                                  <div className="text-blue-300 font-bold text-base mb-2">{hoveredWord.word}</div>
                                  <div className="text-white/90 text-sm mb-3">{hoveredWord.definition}</div>
                                  {hoveredWord.example && (
                                    <div className="text-gray-400 italic text-xs mb-3">"{hoveredWord.example}"</div>
                                  )}
                                  
                                  <div className="flex gap-2">
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        handleWantToLearn(hoveredWord.word, hoveredWord.definition, hoveredWord.example);
                                      }}
                                      className="flex-1 bg-blue-500 hover:bg-blue-600 text-white font-semibold py-2 px-3 rounded-lg text-xs flex items-center justify-center gap-1 transition-colors"
                                    >
                                      <Plus className="w-3 h-3" />
                                      Want to Learn
                                    </button>
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        handleAlreadyKnow(hoveredWord.word);
                                      }}
                                      className="flex-1 bg-gray-700 hover:bg-gray-600 text-white font-semibold py-2 px-3 rounded-lg text-xs flex items-center justify-center gap-1 transition-colors"
                                    >
                                      <Check className="w-3 h-3" />
                                      Already Know
                                    </button>
                                  </div>
                                </>
                              )}
                            </div>
                          </div>
                        )}

                        {userComments.length > 0 && currentVideo.comments_with_slang && currentVideo.comments_with_slang.length > 0 && (
                          <div className="flex items-center gap-3 my-4">
                            <div className="flex-1 h-px bg-gray-700"></div>
                            <span className="text-gray-500 text-xs">Your Comments</span>
                            <div className="flex-1 h-px bg-gray-700"></div>
                          </div>
                        )}

                        {userComments.map(c => (
                          <div key={c.id} className="space-y-2">
                            <div className="flex gap-3">
                              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex-shrink-0"></div>
                              <div className="flex-1">
                                <div className="text-white font-semibold text-sm">{c.user}</div>
                                <div className="text-white/90 text-sm mt-1">{c.text}</div>
                                <div className="flex gap-4 mt-2">
                                  <button className="text-gray-400 text-xs flex items-center gap-1">
                                    <Heart className="w-3 h-3" /> {c.likes}
                                  </button>
                                  <button className="text-gray-400 text-xs">{c.aiResponses.length} Replies</button>
                                </div>
                              </div>
                            </div>
                            {c.aiResponses.map((response, idx) => (
                              <div key={idx} className="flex gap-3 ml-11">
                                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex-shrink-0 flex items-center justify-center text-xs">
                                  AI
                                </div>
                                <div className="flex-1">
                                  <div className="text-white font-semibold text-sm">
                                    {response.authorName || 'AI Coach'}
                                  </div>
                                  <div className="text-white/90 text-sm mt-1">
                                    {response.aiComment || 'No response available'}
                                  </div>
                                  <div className="flex gap-4 mt-2">
                                    <button className="text-gray-400 text-xs flex items-center gap-1">
                                      <Heart className="w-3 h-3" /> {response.likes || Math.floor(Math.random() * 50)}
                                    </button>
                                    <button className="text-gray-400 text-xs">Reply</button>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        ))}
                      </div>

                      <div className="p-4 border-t border-gray-700 bg-gray-800">
                        <div className="flex gap-2">
                          <input
                            type="text"
                            value={comment}
                            onChange={(e) => setComment(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && !isEvaluating && handleSubmitComment()}
                            placeholder={isEvaluating ? "Evaluating..." : "Add a comment..."}
                            disabled={isEvaluating}
                            className="flex-1 bg-gray-700 text-white rounded-full px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50"
                          />
                          <button
                            onClick={handleSubmitComment}
                            disabled={!comment.trim() || isEvaluating}
                            className="p-2 bg-purple-600 rounded-full disabled:opacity-50 disabled:cursor-not-allowed relative"
                          >
                            {isEvaluating ? (
                              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                            ) : (
                              <Send className="w-5 h-5 text-white" />
                            )}
                          </button>
                        </div>
                        {isEvaluating && (
                          <div className="text-white/60 text-xs mt-2 text-center">
                            AI is evaluating your comment...
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </>
        ) : (
          <MySlang
            mySlang={mySlang}
            suggestions={suggestions}
            loadingSuggestions={loadingSuggestions}
          />
        )}
      </div>
    </div>
  );
}