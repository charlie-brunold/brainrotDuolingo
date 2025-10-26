import React, { useState, useEffect } from 'react';
import { Sparkles, Plus, X, ArrowRight } from 'lucide-react';

export default function HomePage({ onStartFetching }) {
  // Add TikTok Sans font
  React.useEffect(() => {
    const link = document.createElement('link');
    link.href = 'https://fonts.cdnfonts.com/css/tiktok-sans';
    link.rel = 'stylesheet';
    document.head.appendChild(link);
    
    document.body.style.fontFamily = "'TikTok Sans', sans-serif";
    
    return () => {
      document.body.style.fontFamily = '';
    };
  }, []);

  const [selectedTopics, setSelectedTopics] = useState([]);
  const [customTopic, setCustomTopic] = useState('');
  const [typedText, setTypedText] = useState('');
  
  const fullText = "Select your interests to customize your language learning experience!";

  // Typing animation effect
  useEffect(() => {
    if (typedText.length < fullText.length) {
      const timeout = setTimeout(() => {
        setTypedText(fullText.slice(0, typedText.length + 1));
      }, 50); // Adjust speed here (lower = faster)
      
      return () => clearTimeout(timeout);
    }
  }, [typedText]);

  // Predefined topic bubbles
  const predefinedTopics = [
    'Gaming',
    'Food Review',
    'Funny Moments',
    'Minecraft',
    'Cooking',
    'Sports',
    'Music',
    'Travel',
    'Fashion',
    'Tech',
    'Fitness',
    'Art',
    'Pets',
    'DIY',
    'Comedy',
    'Dance'
  ];
  
  // Fixed values (not configurable by user)
  const shortsPerTopic = 10;
  const commentsPerShort = 50;

  // Toggle topic selection
  const toggleTopic = (topic) => {
    const lowerTopic = topic.toLowerCase();
    if (selectedTopics.includes(lowerTopic)) {
      // Remove topic if already selected
      setSelectedTopics(selectedTopics.filter(t => t !== lowerTopic));
    } else if (selectedTopics.length < 3) {
      // Add topic only if less than 3 are selected
      setSelectedTopics([...selectedTopics, lowerTopic]);
    } else {
      // Optionally, show a toast or alert
      alert("You can only select up to 3 topics!");
    }
  };

  // Add custom topic
  const addCustomTopic = () => {
    const topicLower = customTopic.trim().toLowerCase();
    if (topicLower && !selectedTopics.includes(topicLower)) {
      setSelectedTopics([...selectedTopics, topicLower]);
      setCustomTopic('');
    }
  };

  // Remove selected topic
  const removeTopic = (topic) => {
    setSelectedTopics(selectedTopics.filter(t => t !== topic));
  };

  // Start fetching
  const handleStart = () => {
    const config = {
      topics: selectedTopics,
      customSlang: [],  // Keep it simple, same as original
      shortsPerTopic: shortsPerTopic,
      commentsPerShort: commentsPerShort
    };
    
    console.log('🚀 Starting with config:', config);
    console.log('🚀 onStartFetching function:', onStartFetching);
    
    if (onStartFetching && typeof onStartFetching === 'function') {
      onStartFetching(config);
    } else {
      console.error('❌ onStartFetching is not a function!', onStartFetching);
      alert('Error: onStartFetching function not provided!');
    }
  };

  return (
    <div className="min-h-screen w-full bg-black flex items-center justify-center p-4" style={{ fontFamily: "'TikTok Sans', sans-serif" }}>
      <div className="max-w-4xl w-full">
        
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Sparkles className="w-10 h-10 text-purple-500" />
            <h1 className="text-4xl font-bold text-white">Brain Thought</h1>
          </div>
          <p className="text-gray-400">
            Select your interests to customize your language learning experience!
          </p>
        </div>

        {/* Main Card */}
        <div className="bg-gray-900 rounded-2xl p-6 space-y-6">
          
          {/* Topics Section */}
          <div>
            <h2 className="text-white text-xl font-medium mb-4">
              Select Your Interests (Up to 3)
            </h2>
            
            {/* Predefined Topic Bubbles */}
            <div className="flex flex-wrap gap-3 mb-6">
              {predefinedTopics.map(topic => {
                const isSelected = selectedTopics.includes(topic.toLowerCase());
                return (
                  <button
                    key={topic}
                    onClick={() => toggleTopic(topic)}
                    className={`px-4 py-2 rounded-full font-medium transition-all ${
                      isSelected
                        ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg shadow-purple-500/50'
                        : 'bg-gray-800 text-gray-300 hover:bg-gray-700 border border-gray-700'
                    }`}
                  >
                    {topic}
                  </button>
                );
              })}
            </div>

            {/* Add Custom Topic */}
            <div className="space-y-3">
              <h3 className="text-white font-semibold text-sm">
                Or add your own:
              </h3>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={customTopic}
                  onChange={(e) => setCustomTopic(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addCustomTopic()}
                  placeholder="Type a custom topic..."
                  className="flex-1 bg-gray-800 text-white rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 placeholder-gray-500 border border-gray-700"
                />
                <button
                  onClick={addCustomTopic}
                  disabled={!customTopic.trim()}
                  className="bg-purple-600 text-white rounded-lg px-4 py-3 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-all"
                >
                  <Plus className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>

          {/* Selected Topics Display */}
          {selectedTopics.length > 0 && (
            <div className="bg-gray-800 rounded-xl p-4">
              <h3 className="text-white font-semibold mb-3 text-sm">
                Selected Topics ({selectedTopics.length})
              </h3>
              <div className="flex flex-wrap gap-2">
                {selectedTopics.map(topic => (
                  <div
                    key={topic}
                    className="bg-gradient-to-r from-purple-600/20 to-pink-600/20 border border-purple-500/50 rounded-full px-4 py-2 flex items-center gap-2"
                  >
                    <span className="text-white text-sm font-medium capitalize">{topic}</span>
                    <button
                      onClick={() => removeTopic(topic)}
                      className="text-white/70 hover:text-red-400 transition-colors"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Warning if no topics selected */}
          {selectedTopics.length === 0 && (
            <div className="bg-yellow-500/10 border border-yellow-500/50 rounded-lg p-4 text-center">
              <p className="text-yellow-400 text-sm">
                ⚠️ Please select at least one topic to continue
              </p>
            </div>
          )}

          {/* Start Button */}
          <button
            onClick={handleStart}
            disabled={selectedTopics.length === 0}
            className={`w-full rounded-xl px-6 py-4 text-lg font-bold transition-all flex items-center justify-center gap-2 ${
              selectedTopics.length === 0
                ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                : 'bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:shadow-lg hover:shadow-purple-500/50'
            }`}
          >
            Start
            <ArrowRight className="w-6 h-6" />
          </button>
        </div>

        {/* Footer Info */}
        <div className="mt-6 text-center text-gray-500 text-sm">
          <p>Relevant videos will be fetched from YouTube.</p>
        </div>

      </div>
    </div>
  );
}