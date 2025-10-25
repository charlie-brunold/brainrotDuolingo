import React from 'react';
import { Sparkles, Lightbulb } from 'lucide-react';

export default function MySlang({
  mySlang,
  suggestions,
  loadingSuggestions
}) {
  return (
    <div className="h-full w-full bg-black overflow-y-auto">
      <div className="p-6">
        {/* Header */}
        <div className="mb-6">
          <h2 className="text-white text-2xl font-bold">My Slang</h2>
          <p className="text-white/60 text-sm">{mySlang.length} {mySlang.length === 1 ? 'term' : 'terms'} learned</p>
        </div>

        {/* Empty State */}
        {mySlang.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-center px-4">
            <Lightbulb className="w-16 h-16 text-yellow-300 mb-4" />
            <h3 className="text-white text-xl font-semibold mb-2">No slang learned yet</h3>
            <p className="text-white/60 text-sm max-w-md">
              Click the 💡 lightbulb icon next to comments with slang to learn new terms and build your vocabulary!
            </p>
          </div>
        ) : (
          <>
            {/* Slang Card Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
              {mySlang.map((slang, index) => (
                <div
                  key={index}
                  className="bg-gradient-to-br from-purple-900/30 to-pink-900/30 rounded-xl p-4 border border-white/10 hover:border-white/30 transition-all"
                >
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="text-white text-xl font-bold">{slang.term}</h3>
                    <Sparkles className="w-5 h-5 text-yellow-300" />
                  </div>
                  <p className="text-white/80 text-sm mb-3">{slang.definition}</p>
                  <div className="bg-black/30 rounded-lg p-2 mb-3">
                    <p className="text-white/60 text-xs italic">"{slang.example}"</p>
                  </div>
                  <div className="flex items-center gap-2 text-white/40 text-xs">
                    <span>From: {slang.videoTitle?.substring(0, 30)}{slang.videoTitle?.length > 30 ? '...' : ''}</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Suggestions Section */}
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
          </>
        )}
      </div>
    </div>
  );
}