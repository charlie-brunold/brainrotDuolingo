import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Heart, MessageCircle, Share2, Bookmark, ChevronUp, ChevronDown, Send, Sparkles, Lightbulb, X, Languages } from 'lucide-react';
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
  const [currentVideoIndex, setCurrentVideoIndex] = useState(0);
  const [showComments, setShowComments] = useState(false);
  const [comment, setComment] = useState('');
  const [userComments, setUserComments] = useState([]);
  const [suggestedSlang, setSuggestedSlang] = useState([]);
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [touchStart, setTouchStart] = useState(0); // NEW: Track Y position on touch start
  const [touchEnd, setTouchEnd] = useState(0);   // NEW: Track Y position on touch end
  const [isEvaluating, setIsEvaluating] = useState(false); // NEW: Loading state for API calls
  const [explanations, setExplanations] = useState({}); // Cache for comment explanations
  const [activeExplanation, setActiveExplanation] = useState(null); // Which comment has tooltip visible
  const [loadingExplanation, setLoadingExplanation] = useState(null); // Which comment is loading
  const [mySlang, setMySlang] = useState(() => {
    // Load from sessionStorage on mount
    const saved = sessionStorage.getItem('brainrot_my_slang');
    return saved ? JSON.parse(saved) : [];
  }); // Array of learned slang with metadata
  const [showMySlang, setShowMySlang] = useState(false); // Toggle for My Slang overlay
  const [suggestions, setSuggestions] = useState([]); // AI-suggested slang terms
  const [loadingSuggestions, setLoadingSuggestions] = useState(false); // Loading state for suggestions
  const [isTranslating, setIsTranslating] = useState(false); // Loading state for translation
  const [translatedText, setTranslatedText] = useState(''); // Translated text
  const [translationAudio, setTranslationAudio] = useState(null); // Audio element for translation
  const [showTranslation, setShowTranslation] = useState(false); // Show translated text overlay
  const [targetLanguage, setTargetLanguage] = useState('Spanish'); // Target language for translation
  const [translationError, setTranslationError] = useState(null); // Error message for translation
  const containerRef = useRef(null);
  const audioRef = useRef(null); // Ref for audio element
  
  // Use provided shortsData or fallback
  const VIDEOS = shortsData || [];
  const currentVideo = VIDEOS[currentVideoIndex];
  const videoId = currentVideo?.url ? currentVideo.url.match(/(?:v=|\/shorts\/)([a-zA-Z0-9_-]{11})/) ? currentVideo.url.match(/(?:v=|\/shorts\/)([a-zA-Z0-9_-]{11})/)[1] : null : null;


  // --- Helper Functions ---

  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num?.toString() || '0';
  };

  const scrollToVideo = (index) => {
    if (index >= 0 && index < VIDEOS.length) {
      setCurrentVideoIndex(index);
      // Reset state for the new video
      setShowComments(false);
      setUserComments([]);
      setComment('');
      setShowFeedback(false);
      setTranslationError(null);
      setShowTranslation(false);
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    }
  };

  // --- Scroll/Swipe Handlers (FIXED/IMPROVED) ---
  
  const handleWheel = (e) => {
    // Prevent scrolling if comments are open
    if (showComments) {
        return; // Do nothing while comments are open
    } 

    // 2. Switch video based on wheel direction
    if (e.deltaY > 0) { // Scroll Down
      scrollToVideo(currentVideoIndex + 1);
    } else { // Scroll Up
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
    const SWIPE_THRESHOLD = 50; // Minimum vertical distance for a swipe

    // Swiping UP (Start Y > End Y)
    if (touchStart - touchEnd > SWIPE_THRESHOLD) {
      scrollToVideo(currentVideoIndex + 1);
    }

    // Swiping DOWN (Start Y < End Y)
    if (touchStart - touchEnd < -SWIPE_THRESHOLD) {
      scrollToVideo(currentVideoIndex - 1);
    }
    
    // Reset touch state
    setTouchStart(0);
    setTouchEnd(0);
  };

  // --- Comment Logic ---

  useEffect(() => {
    if (currentVideo && currentVideo.unique_slang_terms) {
      // Get all slang terms from dictionary
      const allSlangTerms = Object.keys(SLANG_TERMS);

      // Filter out forbidden slang (from example comments)
      const forbiddenSlang = currentVideo.unique_slang_terms.map(s => s.toLowerCase());
      const allowedSlang = allSlangTerms.filter(
        term => !forbiddenSlang.includes(term.toLowerCase())
      );

      // Randomly select 3 alternative slang terms
      const shuffled = [...allowedSlang].sort(() => Math.random() - 0.5);
      const suggestions = shuffled.slice(0, 3);

      setSuggestedSlang(suggestions);
    }
  }, [currentVideoIndex, currentVideo]);

  const addSlangToComment = (slang) => {
    setComment(prev => prev + (prev ? ' ' : '') + slang + ' ');
  };

  // --- API Integration Functions ---

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
          targetLanguage: 'English', // TODO: Make this configurable
          videoLikeCount: currentVideo.like_count || 0,
          availableSlang: currentVideo.unique_slang_terms || [],
          forbiddenSlang: currentVideo.unique_slang_terms || [], // Slang from example comments
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
          targetLanguage: 'English', // TODO: Make this configurable
          availableSlang: currentVideo.unique_slang_terms || [],
          forbiddenSlang: currentVideo.unique_slang_terms || [], // Slang from example comments
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate AI response');
      }

      const data = await response.json();
      // data now contains { responses: [{aiComment, authorName, likes}, ...] }
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
    // If this comment is already showing, just close it
    if (activeExplanation === commentId) {
      setActiveExplanation(null);
      return;
    }

    // If already cached, just show it
    if (explanations[commentId]) {
      setActiveExplanation(commentId);
      return;
    }

    // Otherwise, fetch from API
    setLoadingExplanation(commentId);
    try {
      const explanation = await fetchCommentExplanation(commentId, commentText, detectedSlang);

      // Cache the explanation
      setExplanations(prev => ({
        ...prev,
        [commentId]: explanation
      }));

      // Show the explanation
      setActiveExplanation(commentId);

      // Track slang terms learned (add to My Slang)
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
          // Filter out terms already in mySlang
          const existingTerms = new Set(prev.map(s => s.term.toLowerCase()));
          const uniqueNewTerms = newSlangTerms.filter(
            slang => !existingTerms.has(slang.term.toLowerCase())
          );

          const updated = [...prev, ...uniqueNewTerms];

          // Save to sessionStorage
          sessionStorage.setItem('brainrot_my_slang', JSON.stringify(updated));

          return updated;
        });
      }
    } catch (error) {
      console.error('Failed to get explanation:', error);
      // Show error explanation
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

  // Fetch AI-powered slang suggestions
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

      // Additional frontend filtering: remove duplicates and already-learned terms
      const learnedTermsLower = new Set(mySlang.map(s => s.term.toLowerCase()));
      const seenSuggestions = new Set();
      const filteredSuggestions = (data.suggestions || []).filter(suggestion => {
        const termLower = suggestion.term.toLowerCase();
        // Skip if already learned or duplicate in suggestions
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

  // Fetch suggestions when My Slang overlay is opened
  useEffect(() => {
    if (showMySlang && mySlang.length > 0) {
      fetchSuggestions();
    }
  }, [showMySlang]);

  const handleSubmitComment = async () => {
    if (!comment.trim() || isEvaluating) return;

    setIsEvaluating(true);

    try {
      // Step 1: Evaluate the comment with AI
      const evaluation = await evaluateCommentWithAI(comment);

      // Step 2: Generate multiple AI responses
      const aiResponses = await generateAIResponse(comment, evaluation);

      // Step 3: Create comment with AI responses
      const newComment = {
        id: Date.now(),
        text: comment,
        user: 'You',
        likes: evaluation.likes,
        evaluation,
        aiResponses: aiResponses // Array of {aiComment, authorName, likes}
      };

      setUserComments(prev => [newComment, ...prev]);

      // Step 4: Show feedback
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

      // Show error feedback
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

  const handleTranslateVideo = async () => {
    if (!videoId || isTranslating) return;

    setIsTranslating(true);
    setTranslationError(null); // Clear any previous errors

    try {
      const response = await fetch('http://localhost:3001/api/translate-video', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          video_id: videoId,
          target_language: targetLanguage
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Translation failed');
      }

      const data = await response.json();

      // Set translated text
      setTranslatedText(data.translated_text);
      setShowTranslation(true);

      // Create audio from base64
      const audioBlob = await fetch(`data:audio/mp3;base64,${data.audio_base64}`).then(r => r.blob());
      const audioUrl = URL.createObjectURL(audioBlob);

      // Create and play audio
      const audio = new Audio(audioUrl);
      audioRef.current = audio;

      audio.play();

      // Clean up when audio ends
      audio.onended = () => {
        URL.revokeObjectURL(audioUrl);
      };

    } catch (error) {
      console.error('Error translating video:', error);
      setTranslationError(error.message || 'Translation unavailable. The video may not have captions.');
    } finally {
      setIsTranslating(false);
    }
  };

  const handleStopTranslation = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    setShowTranslation(false);
    setTranslatedText('');
  };

  // --- Render Logic ---

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
      {/* Persistent Header - Fixed at top */}
      <div className="flex-shrink-0 flex justify-center gap-8 p-4 bg-black z-50 border-b border-gray-800">
        <button
          onClick={() => setShowMySlang(true)}
          className={`text-sm font-semibold transition-colors pb-1 ${
            showMySlang
              ? 'text-white border-b-2 border-white'
              : 'text-white/70 hover:text-white'
          }`}
        >
          My Slang {mySlang.length > 0 && `(${mySlang.length})`}
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

      {/* Content Area - Either Video Feed or My Slang */}
      <div className="flex-1 relative overflow-hidden">
        {!showMySlang ? (
          // Video Feed View
          <>
            <div
              ref={containerRef}
              onWheel={handleWheel}
              onTouchStart={handleTouchStart}
              onTouchMove={handleTouchMove}
              onTouchEnd={handleTouchEnd}
              className="absolute inset-0 overflow-hidden"
            >
              {/* Persistent sliding window - keeps adjacent videos mounted */}
              {[currentVideoIndex - 1, currentVideoIndex, currentVideoIndex + 1].map((index, position) => {
                // Skip if index is out of bounds
                if (index < 0 || index >= VIDEOS.length) return null;

                const video = VIDEOS[index];
                const videoIdForIndex = video?.url ? video.url.match(/(?:v=|\/shorts\/)([a-zA-Z0-9_-]{11})/)?.[1] : null;
                const isCurrent = index === currentVideoIndex;

                // Calculate position: previous video (-100%), current (0%), next (+100%)
                const offsetPosition = position - 1; // -1, 0, or 1

                return (
                  <motion.div
                    key={index}
                    className="absolute inset-0 w-full h-full"
                    initial={false}
                    animate={{
                      y: `${offsetPosition * 100}%`,
                    }}
                    transition={{
                      type: 'spring',
                      stiffness: 300,
                      damping: 30,
                      mass: 0.8
                    }}
                  >
                    <div className="w-full h-full flex items-center justify-center bg-black">
                      {videoIdForIndex ? (
                        <iframe
                          key={`iframe-${index}`}
                          width="100%"
                          height="100%"
                          src={`https://www.youtube.com/embed/${videoIdForIndex}?autoplay=${isCurrent ? 1 : 0}&controls=1&rel=0&modestbranding=1`}
                          title={video.title}
                          frameBorder="0"
                          allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                          allowFullScreen
                          className="absolute inset-0"
                          style={{ objectFit: 'cover' }}
                        />
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
                  </motion.div>
                );
              })}
            </div>

            {/* Overlay UI for current video */}
            <div className="absolute inset-0 pointer-events-none">
              <div className="h-full w-full relative pointer-events-auto"
                   style={{ pointerEvents: 'none' }}>
              {/* Video Container with REAL YouTube Video - NOW JUST A PLACEHOLDER FOR POSITIONING */}
              <div className="h-full w-full flex items-center justify-center bg-transparent" style={{ pointerEvents: 'none' }}>
              </div>

        {/* Navigation Arrows */}
        <div className="absolute left-4 top-1/2 transform -translate-y-1/2 flex flex-col gap-4 z-10" style={{ pointerEvents: 'auto' }}>
        <button
            onClick={() => scrollToVideo(currentVideoIndex - 1)}
            disabled={currentVideoIndex === 0 || showComments}
            className="p-3 bg-white/20 backdrop-blur-sm rounded-full disabled:opacity-30 hover:bg-white/30 transition-colors"
        >
            <ChevronUp className="w-6 h-6 text-white" />
        </button>
        <button
            onClick={() => scrollToVideo(currentVideoIndex + 1)}
            disabled={currentVideoIndex === VIDEOS.length - 1 || showComments}
            className="p-3 bg-white/20 backdrop-blur-sm rounded-full disabled:opacity-30 hover:bg-white/30 transition-colors"
        >
            <ChevronDown className="w-6 h-6 text-white" />
        </button>
        </div>
        {/* Right Sidebar */}
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
          <div className="flex flex-col items-center gap-1 relative">
            <button
              onClick={showTranslation ? handleStopTranslation : handleTranslateVideo}
              disabled={isTranslating}
              className={`p-3 backdrop-blur-sm rounded-full transition-colors ${
                showTranslation
                  ? 'bg-green-500/80'
                  : translationError
                  ? 'bg-red-500/80'
                  : 'bg-white/20 hover:bg-white/30'
              } ${isTranslating ? 'opacity-50 cursor-not-allowed' : ''}`}
              title={showTranslation ? 'Stop Translation' : 'Translate to Spanish'}
            >
              {isTranslating ? (
                <div className="w-7 h-7 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <Languages className="w-7 h-7 text-white" />
              )}
            </button>
            <span className="text-white text-xs font-semibold">Translate</span>

            {/* Unavailable Tooltip */}
            {translationError && (
              <motion.div
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 10 }}
                className="absolute right-full mr-3 top-0 w-64 bg-gray-800/95 backdrop-blur-sm rounded-lg shadow-lg p-3 border border-gray-600/50"
              >
                <div className="flex items-start gap-2">
                  <div className="flex-1">
                    <div className="text-white/90 text-xs">{translationError}</div>
                  </div>
                  <button
                    onClick={() => setTranslationError(null)}
                    className="p-1 hover:bg-white/20 rounded-full transition-colors flex-shrink-0"
                  >
                    <X className="w-3 h-3 text-white" />
                  </button>
                </div>
              </motion.div>
            )}
          </div>
          <div className="p-3 bg-white/20 backdrop-blur-sm rounded-full">
            <Share2 className="w-7 h-7 text-white" />
          </div>
          <div className="p-3 bg-white/20 backdrop-blur-sm rounded-full">
            <Bookmark className="w-7 h-7 text-white" />
          </div>
        </div>

        {/* Bottom Info Bar */}
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

        {/* Translation Overlay */}
        {showTranslation && translatedText && (
          <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black via-black/90 to-transparent z-30 max-h-48 overflow-y-auto"
               style={{ pointerEvents: 'auto' }}>
            <div className="flex items-start gap-2 mb-2">
              <Languages className="w-5 h-5 text-green-400 flex-shrink-0 mt-1" />
              <div className="flex-1">
                <div className="text-green-400 font-semibold text-sm mb-1">Translation ({targetLanguage})</div>
                <div className="text-white text-sm">{translatedText}</div>
              </div>
              <button
                onClick={handleStopTranslation}
                className="p-1 hover:bg-white/10 rounded-full transition-colors"
              >
                <X className="w-5 h-5 text-white" />
              </button>
            </div>
          </div>
        )}

        {/* Comments Section Overlay */}
        {showComments && (
          <div
            className="absolute inset-0 bg-black/50 z-40"
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
                <h3 className="text-white font-bold text-lg">{formatNumber(currentVideo.slang_comment_count || 0)} Comments with Slang</h3>
              </div>

              {/* Practice Prompt */}
              <div className="p-4 bg-gradient-to-r from-purple-600 to-pink-600">
                <div className="flex items-start gap-2">
                  <Sparkles className="w-5 h-5 text-white flex-shrink-0 mt-1" />
                  <div>
                    <div className="text-white font-semibold mb-1">Use NEW slang (not from examples!)</div>
                    <div className="text-white/90 text-sm">Try different slang than what's in the comments</div>
                    <div className="mt-2 flex flex-wrap gap-2">
                      <span className="text-white/80 text-xs">Suggested:</span>
                      {suggestedSlang.map(slang => (
                        <button
                          key={slang}
                          onClick={() => addSlangToComment(slang)}
                          className="px-2 py-1 bg-white/20 backdrop-blur-sm rounded-full text-xs text-white hover:bg-white/30"
                        >
                          {slang}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Feedback */}
              {showFeedback && feedback && (
                <div className="p-4 bg-blue-600 border-b border-gray-700">
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
                          ✗ Mistakes: {feedback.mistakes.join(', ')}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Comments List */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
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
                    {/* AI Responses */}
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
                
                {/* Show real comments from the video */}
                {currentVideo.comments_with_slang && currentVideo.comments_with_slang.slice(0, 5).map((c, idx) => {
                  const commentId = c.comment_id;
                  const isExplaining = activeExplanation === commentId;
                  const isLoading = loadingExplanation === commentId;
                  const explanation = explanations[commentId];

                  return (
                    <div key={commentId} className="relative">
                      <div className="flex gap-3">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-green-500 to-teal-500 flex-shrink-0"></div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <div className="text-white font-semibold text-sm">{c.author}</div>
                            <button
                              onClick={() => handleExplainClick(commentId, c.text, c.detected_slang)}
                              disabled={isLoading}
                              className="p-1 bg-white/10 backdrop-blur-sm rounded-full hover:bg-white/20 transition-colors disabled:opacity-50"
                              title="Explain this comment"
                            >
                              {isLoading ? (
                                <div className="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin" />
                              ) : (
                                <Lightbulb className="w-3 h-3 text-yellow-300" />
                              )}
                            </button>
                          </div>
                          <div className="text-white/90 text-sm mt-1">{c.text}</div>

                          {/* Tooltip/Bubble for Explanation */}
                          {isExplaining && explanation && (
                            <div className="mt-3 p-3 bg-gray-800 rounded-lg shadow-lg border border-gray-700 relative">
                              <button
                                onClick={() => setActiveExplanation(null)}
                                className="absolute top-2 right-2 p-1 hover:bg-gray-700 rounded-full transition-colors"
                              >
                                <X className="w-3 h-3 text-gray-400" />
                              </button>

                              <div className="text-white/90 text-xs mb-2">
                                <span className="font-semibold text-blue-400">Translation:</span> {explanation.translation}
                              </div>

                              {explanation.slangBreakdown && explanation.slangBreakdown.length > 0 && (
                                <div className="text-white/80 text-xs">
                                  <div className="font-semibold text-purple-400 mb-1">Slang Breakdown:</div>
                                  {explanation.slangBreakdown.map((item, i) => (
                                    <div key={i} className="ml-2 mb-1">
                                      <span className="text-yellow-300 font-semibold">{item.term}:</span> {item.definition}
                                      <div className="text-gray-400 italic ml-2">"{item.usage}"</div>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          )}

                          <div className="flex gap-4 mt-2">
                            <button className="text-gray-400 text-xs flex items-center gap-1">
                              <Heart className="w-3 h-3" /> {c.like_count}
                            </button>
                            <span className="text-purple-400 text-xs">
                              {c.detected_slang.join(', ')}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Comment Input */}
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
          // My Slang View
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