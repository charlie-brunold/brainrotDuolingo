import React, { useState, useMemo } from 'react';
import { Sparkles, Lightbulb, Search, BookOpen, GraduationCap, X, Library } from 'lucide-react';

export default function MySlang({
  mySlang,
  suggestions,
  loadingSuggestions,
  knownWords = [] // Pass this from parent
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('all'); // 'all', 'learning' or 'known'

  // Filter slang based on search query
  const filteredSlang = useMemo(() => {
    if (!searchQuery.trim()) return mySlang;
    
    const query = searchQuery.toLowerCase();
    return mySlang.filter(slang => 
      slang.term.toLowerCase().includes(query) ||
      slang.definition.toLowerCase().includes(query) ||
      slang.example.toLowerCase().includes(query)
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

  return (
    <div className="h-full w-full bg-black overflow-y-auto">
      <div className="p-6">
        {/* Header with Search */}
        <div className="mb-6">
          <h2 className="text-white text-2xl font-bold mb-4">My Words</h2>
          
          {/* Search Bar */}
          <div className="relative mb-4">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-white/40" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search your words..."
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
                Learning
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
                Known
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
                      Words I'm Learning ({filteredAllWords.filter(w => w.type === 'learning').length})
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {filteredAllWords
                        .filter(w => w.type === 'learning')
                        .map((word, index) => (
                          <div
                            key={`learning-${index}`}
                            className="bg-gradient-to-br from-purple-900/30 to-pink-900/30 rounded-xl p-4 border border-white/10 hover:border-white/30 transition-all"
                          >
                            <div className="flex justify-between items-start mb-2">
                              <h3 className="text-white text-xl font-bold">{word.term}</h3>
                              <Sparkles className="w-5 h-5 text-yellow-300" />
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
                      Words I Know ({filteredAllWords.filter(w => w.type === 'known').length})
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                      {filteredAllWords
                        .filter(w => w.type === 'known')
                        .map((word, index) => (
                          <div
                            key={`known-${index}`}
                            className="bg-gradient-to-br from-green-900/20 to-emerald-900/20 rounded-lg p-4 border border-green-500/20 hover:border-green-500/40 transition-all"
                          >
                            <div className="flex items-center gap-2">
                              <BookOpen className="w-4 h-4 text-green-400" />
                              <h3 className="text-white text-lg font-semibold">{word.term}</h3>
                            </div>
                            <p className="text-green-300 text-xs mt-2">Already mastered ✓</p>
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
                <Lightbulb className="w-16 h-16 text-yellow-300 mb-4" />
                <h3 className="text-white text-xl font-semibold mb-2">No slang learned yet</h3>
                <p className="text-white/60 text-sm max-w-md">
                  Hover over words in comments and click "Want to Learn" to start building your vocabulary!
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
                      className="bg-gradient-to-br from-purple-900/30 to-pink-900/30 rounded-xl p-4 border border-white/10 hover:border-white/30 transition-all"
                    >
                      <div className="flex justify-between items-start mb-2">
                        <h3 className="text-white text-xl font-bold">{slang.term}</h3>
                        <Sparkles className="w-5 h-5 text-yellow-300" />
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

                {/* Suggestions Section */}
                {!searchQuery && (
                  <div className="border-t border-white/10 pt-6">
                    <div className="flex items-center gap-2 mb-4">
                      <Sparkles className="w-5 h-5 text-purple-400" />
                      <h3 className="text-white text-lg font-semibold">Suggested for You</h3>
                      <span className="text-white/40 text-xs">AI-powered recommendations</span>
                    </div>

                    {loadingSuggestions ? (
                      <div className="flex items-center justify-center h-32">
                        <div className="w-8 h-8 border-4 border-purple-400 border-t-transparent rounded-full animate-spin"></div>
                      </div>
                    ) : suggestions.length > 0 ? (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {suggestions.map((suggestion) => (
                          <div
                            key={suggestion.term}
                            className="bg-gradient-to-r from-purple-900/20 to-blue-900/20 rounded-lg p-4 border border-purple-500/30 hover:border-purple-500/60 transition-all cursor-pointer"
                          >
                            <div className="flex justify-between items-start mb-2">
                              <h4 className="text-white font-semibold">{suggestion.term}</h4>
                              <span className="text-xs text-purple-300 bg-purple-500/20 px-2 py-1 rounded">
                                {suggestion.category}
                              </span>
                            </div>
                            <p className="text-white/70 text-sm mb-2">{suggestion.definition}</p>
                            <p className="text-purple-300 text-xs italic">{suggestion.reason}</p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-white/60 text-sm">
                        Learn a few more slang terms to get personalized suggestions!
                      </p>
                    )}
                  </div>
                )}
              </>
            )}
          </>
        ) : (
          <>
            {/* Words I Know Tab */}
            {knownWordsData.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-64 text-center px-4">
                <BookOpen className="w-16 h-16 text-green-300 mb-4" />
                <h3 className="text-white text-xl font-semibold mb-2">No words marked as known</h3>
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
                    className="bg-gradient-to-br from-green-900/20 to-emerald-900/20 rounded-lg p-4 border border-green-500/20 hover:border-green-500/40 transition-all"
                  >
                    <div className="flex items-center gap-2">
                      <BookOpen className="w-4 h-4 text-green-400" />
                      <h3 className="text-white text-lg font-semibold">{word.term}</h3>
                    </div>
                    <p className="text-green-300 text-xs mt-2">Already mastered ✓</p>
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