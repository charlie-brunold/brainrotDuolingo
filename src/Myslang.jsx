import React, { useState, useMemo } from 'react';
import { Sparkles, Search, BookOpen, GraduationCap, X, Library, Trash2 } from 'lucide-react';

export default function MySlang({
  mySlang,
  setMySlang,
  knownWords,
  setKnownWords,
  suggestions,
  loadingSuggestions
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('all');

  // Filter slang based on search query
  const filteredSlang = useMemo(() => {
    if (!searchQuery.trim()) return mySlang;
    
    const query = searchQuery.toLowerCase();
    return mySlang.filter(slang => 
      slang.term.toLowerCase().includes(query) ||
      slang.definition.toLowerCase().includes(query) ||
      slang.example?.toLowerCase().includes(query)
    );
  }, [mySlang, searchQuery]);

  // Get words I already know (marked as known but not in learning)
  const knownWordsData = useMemo(() => {
    return knownWords
      .filter(word => !mySlang.some(s => s.term.toLowerCase() === word.toLowerCase()))
      .map(word => ({
        term: word,
        isKnown: true
      }));
  }, [knownWords, mySlang]);

  // Filter known words based on search
  const filteredKnownWords = useMemo(() => {
    if (!searchQuery.trim()) return knownWordsData;
    
    const query = searchQuery.toLowerCase();
    return knownWordsData.filter(word => 
      word.term.toLowerCase().includes(query)
    );
  }, [knownWordsData, searchQuery]);

  // Combined all words
  const allWords = useMemo(() => {
    return [
      ...mySlang.map(s => ({ ...s, type: 'learning' })),
      ...knownWordsData.map(w => ({ ...w, type: 'known' }))
    ];
  }, [mySlang, knownWordsData]);

  // Filter all words based on search
  const filteredAllWords = useMemo(() => {
    if (!searchQuery.trim()) return allWords;
    
    const query = searchQuery.toLowerCase();
    return allWords.filter(word => {
      if (word.type === 'learning') {
        return word.term.toLowerCase().includes(query) ||
               word.definition?.toLowerCase().includes(query) ||
               word.example?.toLowerCase().includes(query);
      } else {
        return word.term.toLowerCase().includes(query);
      }
    });
  }, [allWords, searchQuery]);

  const clearSearch = () => {
    setSearchQuery('');
  };

  const totalWords = mySlang.length + knownWordsData.length;

  // Remove a learning word
  const removeFromLearning = (term) => {
    const updated = mySlang.filter(s => s.term.toLowerCase() !== term.toLowerCase());
    setMySlang(updated);
    sessionStorage.setItem('brainrot_my_slang', JSON.stringify(updated));
  };

  // Remove a known word
  const removeFromKnown = (term) => {
    const updated = knownWords.filter(w => w.toLowerCase() !== term.toLowerCase());
    setKnownWords(updated);
    sessionStorage.setItem('brainrot_known_words', JSON.stringify(updated));
  };

  // Move from learning to known
  const moveToKnown = (term) => {
    // Add to known words
    const updatedKnown = [...knownWords, term];
    setKnownWords(updatedKnown);
    sessionStorage.setItem('brainrot_known_words', JSON.stringify(updatedKnown));
    
    // Remove from learning
    removeFromLearning(term);
  };

  // Move from known to learning
  const moveToLearning = (term, definition = 'No definition available', example = '') => {
    // Add to learning
    const newSlangTerm = {
      term: term,
      definition: definition,
      example: example,
      learnedAt: Date.now()
    };
    const updatedLearning = [...mySlang, newSlangTerm];
    setMySlang(updatedLearning);
    sessionStorage.setItem('brainrot_my_slang', JSON.stringify(updatedLearning));
    
    // Remove from known
    removeFromKnown(term);
  };

  return (
    <div className="h-full w-full bg-black overflow-y-auto">
      <div className="p-6">
        {/* Header with Search */}
        <div className="mb-6">
          <h2 className="text-white text-2xl font-bold mb-4">My Vocabulary</h2>
          
          {/* Search Bar */}
          <div className="relative mb-4">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-white/40" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search your vocabulary..."
              className="w-full bg-gray-800 text-white rounded-full pl-10 pr-10 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 border border-white/10"
            />
            {searchQuery && (
              <button
                onClick={clearSearch}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-white/40 hover:text-white/80 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>

          {/* Tabs */}
          <div className="flex gap-4 border-b border-white/10 overflow-x-auto">
            <button
              onClick={() => setActiveTab('all')}
              className={`pb-3 px-2 font-semibold text-sm transition-colors relative whitespace-nowrap ${
                activeTab === 'all'
                  ? 'text-blue-400'
                  : 'text-white/60 hover:text-white/80'
              }`}
            >
              <div className="flex items-center gap-2">
                <Library className="w-4 h-4" />
                All Words
                <span className="bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded-full text-xs">
                  {totalWords}
                </span>
              </div>
              {activeTab === 'all' && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-400"></div>
              )}
            </button>

            <button
              onClick={() => setActiveTab('learning')}
              className={`pb-3 px-2 font-semibold text-sm transition-colors relative whitespace-nowrap ${
                activeTab === 'learning'
                  ? 'text-purple-400'
                  : 'text-white/60 hover:text-white/80'
              }`}
            >
              <div className="flex items-center gap-2">
                <GraduationCap className="w-4 h-4" />
                Want to Learn
                <span className="bg-purple-500/20 text-purple-300 px-2 py-0.5 rounded-full text-xs">
                  {mySlang.length}
                </span>
              </div>
              {activeTab === 'learning' && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-purple-400"></div>
              )}
            </button>
            
            <button
              onClick={() => setActiveTab('known')}
              className={`pb-3 px-2 font-semibold text-sm transition-colors relative whitespace-nowrap ${
                activeTab === 'known'
                  ? 'text-green-400'
                  : 'text-white/60 hover:text-white/80'
              }`}
            >
              <div className="flex items-center gap-2">
                <BookOpen className="w-4 h-4" />
                Already Know
                <span className="bg-green-500/20 text-green-300 px-2 py-0.5 rounded-full text-xs">
                  {knownWordsData.length}
                </span>
              </div>
              {activeTab === 'known' && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-green-400"></div>
              )}
            </button>
          </div>
        </div>

        {/* Content based on active tab */}
        {activeTab === 'all' ? (
          <>
            {/* All Words Tab */}
            {totalWords === 0 ? (
              <div className="flex flex-col items-center justify-center h-64 text-center px-4">
                <Library className="w-16 h-16 text-blue-300 mb-4" />
                <h3 className="text-white text-xl font-semibold mb-2">No words yet</h3>
                <p className="text-white/60 text-sm max-w-md">
                  Start hovering over words in comments to build your vocabulary!
                </p>
              </div>
            ) : filteredAllWords.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-64 text-center px-4">
                <Search className="w-16 h-16 text-white/40 mb-4" />
                <h3 className="text-white text-xl font-semibold mb-2">No results found</h3>
                <p className="text-white/60 text-sm">
                  Try a different search term
                </p>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Learning Words Section */}
                {filteredAllWords.some(w => w.type === 'learning') && (
                  <div>
                    <h3 className="text-purple-400 font-semibold mb-3 flex items-center gap-2">
                      <GraduationCap className="w-4 h-4" />
                      Want to Learn ({filteredAllWords.filter(w => w.type === 'learning').length})
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {filteredAllWords
                        .filter(w => w.type === 'learning')
                        .map((word, index) => (
                          <div
                            key={`learning-${index}`}
                            className="bg-gradient-to-br from-purple-900/30 to-pink-900/30 rounded-xl p-4 border border-white/10 hover:border-white/30 transition-all group"
                          >
                            <div className="flex justify-between items-start mb-2">
                              <h3 className="text-white text-xl font-bold">{word.term}</h3>
                              <div className="flex gap-2">
                                <button
                                  onClick={() => moveToKnown(word.term)}
                                  className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-green-500/20 rounded"
                                  title="Mark as known"
                                >
                                  <BookOpen className="w-4 h-4 text-green-400" />
                                </button>
                                <button
                                  onClick={() => removeFromLearning(word.term)}
                                  className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-red-500/20 rounded"
                                  title="Remove"
                                >
                                  <Trash2 className="w-4 h-4 text-red-400" />
                                </button>
                              </div>
                            </div>
                            <p className="text-white/80 text-sm mb-3">{word.definition}</p>
                            {word.example && (
                              <div className="bg-black/30 rounded-lg p-2 mb-3">
                                <p className="text-white/60 text-xs italic">"{word.example}"</p>
                              </div>
                            )}
                            {word.videoTitle && (
                              <div className="flex items-center gap-2 text-white/40 text-xs">
                                <span>From: {word.videoTitle?.substring(0, 30)}{word.videoTitle?.length > 30 ? '...' : ''}</span>
                              </div>
                            )}
                          </div>
                        ))}
                    </div>
                  </div>
                )}

                {/* Known Words Section */}
                {filteredAllWords.some(w => w.type === 'known') && (
                  <div>
                    <h3 className="text-green-400 font-semibold mb-3 flex items-center gap-2">
                      <BookOpen className="w-4 h-4" />
                      Already Know ({filteredAllWords.filter(w => w.type === 'known').length})
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                      {filteredAllWords
                        .filter(w => w.type === 'known')
                        .map((word, index) => (
                          <div
                            key={`known-${index}`}
                            className="bg-gradient-to-br from-green-900/20 to-emerald-900/20 rounded-lg p-4 border border-green-500/20 hover:border-green-500/40 transition-all group"
                          >
                            <div className="flex items-start justify-between gap-2">
                              <div className="flex items-center gap-2 flex-1">
                                <BookOpen className="w-4 h-4 text-green-400 flex-shrink-0" />
                                <h3 className="text-white text-lg font-semibold break-words">{word.term}</h3>
                              </div>
                              <button
                                onClick={() => removeFromKnown(word.term)}
                                className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-red-500/20 rounded flex-shrink-0"
                                title="Remove"
                              >
                                <Trash2 className="w-3 h-3 text-red-400" />
                              </button>
                            </div>
                            <p className="text-green-300 text-xs mt-2">Mastered ✓</p>
                          </div>
                        ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </>
        ) : activeTab === 'learning' ? (
          <>
            {/* Empty State for Learning */}
            {mySlang.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-64 text-center px-4">
                <GraduationCap className="w-16 h-16 text-purple-300 mb-4" />
                <h3 className="text-white text-xl font-semibold mb-2">No words to learn yet</h3>
                <p className="text-white/60 text-sm max-w-md">
                  Hover over words in comments and click "Want to Learn" to add them here!
                </p>
              </div>
            ) : filteredSlang.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-64 text-center px-4">
                <Search className="w-16 h-16 text-white/40 mb-4" />
                <h3 className="text-white text-xl font-semibold mb-2">No results found</h3>
                <p className="text-white/60 text-sm">
                  Try a different search term
                </p>
              </div>
            ) : (
              <>
                {/* Slang Card Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
                  {filteredSlang.map((slang, index) => (
                    <div
                      key={index}
                      className="bg-gradient-to-br from-purple-900/30 to-pink-900/30 rounded-xl p-4 border border-white/10 hover:border-white/30 transition-all group"
                    >
                      <div className="flex justify-between items-start mb-2">
                        <h3 className="text-white text-xl font-bold">{slang.term}</h3>
                        <div className="flex gap-2">
                          <button
                            onClick={() => moveToKnown(slang.term)}
                            className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-green-500/20 rounded"
                            title="Mark as known"
                          >
                            <BookOpen className="w-4 h-4 text-green-400" />
                          </button>
                          <button
                            onClick={() => removeFromLearning(slang.term)}
                            className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-red-500/20 rounded"
                            title="Remove"
                          >
                            <Trash2 className="w-4 h-4 text-red-400" />
                          </button>
                        </div>
                      </div>
                      <p className="text-white/80 text-sm mb-3">{slang.definition}</p>
                      {slang.example && (
                        <div className="bg-black/30 rounded-lg p-2 mb-3">
                          <p className="text-white/60 text-xs italic">"{slang.example}"</p>
                        </div>
                      )}
                      {slang.videoTitle && (
                        <div className="flex items-center gap-2 text-white/40 text-xs">
                          <span>From: {slang.videoTitle?.substring(0, 30)}{slang.videoTitle?.length > 30 ? '...' : ''}</span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>

               

              </>
            )}
          </>
        ) : (
          <>
            {/* Already Know Tab */}
            {knownWordsData.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-64 text-center px-4">
                <BookOpen className="w-16 h-16 text-green-300 mb-4" />
                <h3 className="text-white text-xl font-semibold mb-2">No known words yet</h3>
                <p className="text-white/60 text-sm max-w-md">
                  When you hover over words you already know, click "Already Know" to track them here!
                </p>
              </div>
            ) : filteredKnownWords.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-64 text-center px-4">
                <Search className="w-16 h-16 text-white/40 mb-4" />
                <h3 className="text-white text-xl font-semibold mb-2">No results found</h3>
                <p className="text-white/60 text-sm">
                  Try a different search term
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                {filteredKnownWords.map((word, index) => (
                  <div
                    key={index}
                    className="bg-gradient-to-br from-green-900/20 to-emerald-900/20 rounded-lg p-4 border border-green-500/20 hover:border-green-500/40 transition-all group"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2 flex-1">
                        <BookOpen className="w-4 h-4 text-green-400 flex-shrink-0" />
                        <h3 className="text-white text-lg font-semibold break-words">{word.term}</h3>
                      </div>
                      <button
                        onClick={() => removeFromKnown(word.term)}
                        className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-red-500/20 rounded flex-shrink-0"
                        title="Remove"
                      >
                        <Trash2 className="w-3 h-3 text-red-400" />
                      </button>
                    </div>
                    <p className="text-green-300 text-xs mt-2">Mastered ✓</p>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}