import React, { useState, useRef, useEffect } from 'react';
import { Heart, MessageCircle, Share2, Bookmark, ChevronUp, ChevronDown, Send, Sparkles } from 'lucide-react';

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
  const containerRef = useRef(null);
  
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
    }
  };

  // --- Scroll/Swipe Handlers (FIXED/IMPROVED) ---
  
  const handleWheel = (e) => {
    // 1. If comments are open, close them on the first scroll event.
    if (showComments) {
        setShowComments(false);
        return; // Prevents accidental video skip on closing gesture
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
      const suggestions = currentVideo.unique_slang_terms.slice(0, 3);
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
          videoViewCount: currentVideo.view_count || 0,
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
          targetLanguage: 'English', // TODO: Make this configurable
          availableSlang: currentVideo.unique_slang_terms || [],
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
    <div className="h-screen w-full bg-black relative"> {/* Removed overflow-y-auto */}
      <div
        ref={containerRef}
        onWheel={handleWheel}
        onTouchStart={handleTouchStart} // ADDED
        onTouchMove={handleTouchMove}   // ADDED
        onTouchEnd={handleTouchEnd}     // ADDED
        className="h-full w-full relative"
      >
        {/* Video Container with REAL YouTube Video */}
        <div className="h-full w-full flex items-center justify-center bg-black">
          {videoId ? (
            <iframe
              width="100%"
              height="100%"
              src={`https://www.youtube.com/embed/${videoId}?autoplay=0&controls=1&rel=0&modestbranding=1`}
              title={currentVideo.title}
              frameBorder="0"
              allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
              allowFullScreen
              className="absolute inset-0"
              style={{ objectFit: 'cover' }}
            />
          ) : (
            <div className="text-center text-white p-8">
              <img 
                src={currentVideo.thumbnail} 
                alt={currentVideo.title}
                className="max-w-full max-h-full rounded-lg mb-4"
              />
              <div className="text-2xl font-bold mb-2">{currentVideo.title}</div>
              <div className="text-lg opacity-80">@{currentVideo.channel}</div>
            </div>
          )}
        </div>

        {/* Navigation Arrows */}
        <div className="absolute right-4 top-1/2 transform -translate-y-1/2 flex flex-col gap-4 z-20">
          <button
            onClick={() => scrollToVideo(currentVideoIndex - 1)}
            disabled={currentVideoIndex === 0 || showComments} // Added showComments disable
            className="p-3 bg-white/20 backdrop-blur-sm rounded-full disabled:opacity-30"
          >
            <ChevronUp className="w-6 h-6 text-white" />
          </button>
          <button
            onClick={() => scrollToVideo(currentVideoIndex + 1)}
            disabled={currentVideoIndex === VIDEOS.length - 1 || showComments} // Added showComments disable
            className="p-3 bg-white/20 backdrop-blur-sm rounded-full disabled:opacity-30"
          >
            <ChevronDown className="w-6 h-6 text-white" />
          </button>
        </div>

        {/* Right Sidebar */}
        <div className="absolute right-4 bottom-24 flex flex-col gap-6 items-center z-10">
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

        {/* Bottom Info Bar */}
        <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/80 to-transparent z-10">
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

        {/* Comments Section Overlay */}
        {showComments && (
          <div 
            className="absolute inset-0 bg-black/50 z-30"
            onClick={() => setShowComments(false)}
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
                    <div className="text-white font-semibold mb-1">Practice with real comments!</div>
                    <div className="text-white/90 text-sm">Try using the slang from this video</div>
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
                            {response.authorName || response}
                          </div>
                          <div className="text-white/90 text-sm mt-1">
                            {response.aiComment || response}
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
                {currentVideo.comments_with_slang && currentVideo.comments_with_slang.slice(0, 5).map((c, idx) => (
                  <div key={`real-${idx}`} className="flex gap-3">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-green-500 to-teal-500 flex-shrink-0"></div>
                    <div className="flex-1">
                      <div className="text-white font-semibold text-sm">{c.author}</div>
                      <div className="text-white/90 text-sm mt-1">{c.text}</div>
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
                ))}
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

        {/* Top Bar */}
        <div className="absolute top-0 left-0 right-0 p-4 flex justify-center gap-8 z-10">
          <button className="text-white/70 text-sm font-semibold">Following</button>
          <button className="text-white text-sm font-bold border-b-2 border-white pb-1">For You</button>
        </div>
      </div>
    </div>
  );
}