import React, { useState } from 'react';
import { Sparkles, Plus, X, Play, ArrowRight } from 'lucide-react';

export default function HomePage({ onStartFetching }) {
  const [topics, setTopics] = useState([]);
  const [newTopic, setNewTopic] = useState('');
  const [customSlang, setCustomSlang] = useState([]);
  const [newSlang, setNewSlang] = useState('');
  const [useDefaults, setUseDefaults] = useState(false);

  const defaultTopics = ['gaming', 'food review', 'funny moments'];
  
  // Fixed values (not configurable by user)
  const shortsPerTopic = 10;
  const commentsPerShort = 50;

  // Add topic
  const addTopic = () => {
    if (newTopic.trim() && !topics.includes(newTopic.trim().toLowerCase())) {
      setTopics([...topics, newTopic.trim().toLowerCase()]);
      setNewTopic('');
    }
  };

  // Remove topic
  const removeTopic = (topic) => {
    setTopics(topics.filter(t => t !== topic));
  };

  // Add custom slang
  const addSlang = () => {
    if (newSlang.trim() && !customSlang.includes(newSlang.trim().toLowerCase())) {
      setCustomSlang([...customSlang, newSlang.trim().toLowerCase()]);
      setNewSlang('');
    }
  };

  // Remove custom slang
  const removeSlang = (slang) => {
    setCustomSlang(customSlang.filter(s => s !== slang));
  };

  // Toggle default topics
  const toggleDefaults = () => {
    if (useDefaults) {
      setTopics(topics.filter(t => !defaultTopics.includes(t)));
    } else {
      setTopics([...new Set([...topics, ...defaultTopics])]);
    }
    setUseDefaults(!useDefaults);
  };

 // Start fetching
const handleStart = () => {
  const finalTopics = topics.length > 0 ? topics : defaultTopics;
  
  const config = {
    topics: finalTopics,
    customSlang: customSlang,
    shortsPerTopic: shortsPerTopic,
    commentsPerShort: commentsPerShort
  };
  
  console.log('🚀 Starting with config:', config);
  
  if (onStartFetching && typeof onStartFetching === 'function') {
    onStartFetching(config);
  } else {
    console.error('❌ onStartFetching is not a function!', onStartFetching);
    alert('Error: onStartFetching function not provided!');
  }
};

  // Can start if has topics OR will use defaults
  const canStart = topics.length > 0 || true; // Always allow start (will use defaults if no topics)

  return (
    <div className="min-h-screen w-full bg-black flex items-center justify-center p-4">
      <div className="max-w-2xl w-full">
        
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Sparkles className="w-10 h-10 text-purple-500" />
            <h1 className="text-4xl font-bold text-white">Brainrot TikTok</h1>
          </div>
          <p className="text-gray-400">
            Customize your slang learning experience
          </p>
        </div>

        {/* Main Card */}
        <div className="bg-gray-900 rounded-2xl p-6 space-y-6">
          
          {/* Topics Section */}
          <div>
            <h2 className="text-white text-xl font-bold mb-3 flex items-center gap-2">
              🎯 Choose Topics
              <span className="text-sm font-normal text-gray-400">(Required)</span>
            </h2>
            
            {/* Use Defaults Checkbox */}
            <label className="flex items-center gap-3 mb-4 cursor-pointer bg-gray-800 p-3 rounded-lg hover:bg-gray-750">
              <input
                type="checkbox"
                checked={useDefaults}
                onChange={toggleDefaults}
                className="w-5 h-5 rounded bg-gray-700 border-gray-600 text-purple-600 focus:ring-purple-500"
              />
              <div className="flex-1">
                <div className="text-white font-semibold">Use Default Topics</div>
                <div className="text-gray-400 text-sm">
                  {defaultTopics.join(', ')}
                </div>
              </div>
            </label>

            {/* Add Custom Topic */}
            <div className="flex gap-2 mb-3">
              <input
                type="text"
                value={newTopic}
                onChange={(e) => setNewTopic(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && addTopic()}
                placeholder="Add custom topic (e.g., minecraft, cooking)"
                className="flex-1 bg-gray-800 text-white rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 placeholder-gray-500"
              />
              <button
                onClick={addTopic}
                disabled={!newTopic.trim()}
                className="bg-purple-600 text-white rounded-lg px-4 py-3 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                <Plus className="w-5 h-5" />
              </button>
            </div>

            {/* Selected Topics */}
            {topics.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {topics.map(topic => (
                  <div
                    key={topic}
                    className="bg-purple-600/20 border border-purple-500 rounded-full px-3 py-2 flex items-center gap-2"
                  >
                    <span className="text-white text-sm">{topic}</span>
                    <button
                      onClick={() => removeTopic(topic)}
                      className="text-white hover:text-red-400"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            {topics.length === 0 && (
              <div className="bg-yellow-500/10 border border-yellow-500/50 rounded-lg p-3 text-center">
                <p className="text-yellow-400 text-sm">
                  ⚠️ Add at least one topic to continue
                </p>
              </div>
            )}
          </div>

          {/* Custom Slang Section */}
          <div>
            <h2 className="text-white text-xl font-bold mb-3 flex items-center gap-2">
              📝 Custom Slang
              <span className="text-sm font-normal text-gray-400">(Optional)</span>
            </h2>
            <p className="text-gray-400 text-sm mb-3">
              Add your own slang terms to track in comments
            </p>

            {/* Add Custom Slang */}
            <div className="flex gap-2 mb-3">
              <input
                type="text"
                value={newSlang}
                onChange={(e) => setNewSlang(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && addSlang()}
                placeholder="Add slang term (e.g., yeet, vibe, goated)"
                className="flex-1 bg-gray-800 text-white rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 placeholder-gray-500"
              />
              <button
                onClick={addSlang}
                disabled={!newSlang.trim()}
                className="bg-purple-600 text-white rounded-lg px-4 py-3 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                <Plus className="w-5 h-5" />
              </button>
            </div>

            {/* Selected Slang */}
            {customSlang.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {customSlang.map(slang => (
                  <div
                    key={slang}
                    className="bg-pink-600/20 border border-pink-500 rounded-full px-3 py-2 flex items-center gap-2"
                  >
                    <span className="text-white text-sm">{slang}</span>
                    <button
                      onClick={() => removeSlang(slang)}
                      className="text-white hover:text-red-400"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Start Button */}
          <button
            onClick={handleStart}
            className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl px-6 py-4 text-lg font-bold hover:opacity-90 transition-all"
          >
            <Play className="w-6 h-6 inline mr-2" />
            Start Fetching Videos
            <ArrowRight className="w-6 h-6 inline ml-2" />
          </button>

          {topics.length === 0 && (
            <p className="text-center text-yellow-400 text-sm">
              No topics selected - will use defaults: {defaultTopics.join(', ')}
            </p>
          )}
        </div>

        {/* Footer Info */}
        <div className="mt-6 text-center text-gray-500 text-sm">
          <p>Videos will be fetched from YouTube with slang comments</p>
          <p className="mt-1">Default slang terms: fr, ngl, bussin, sigma, rizz, and more</p>
        </div>

      </div>
    </div>
  );
}