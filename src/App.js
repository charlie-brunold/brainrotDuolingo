import React, { useState } from 'react';
import HomePage from './Homepage';
import BrainrotTikTok from './Brainrottiktok.jsx';
import RefreshSlangButton from './RefreshButton.jsx';

function App() {
  const [showHomePage, setShowHomePage] = useState(true);
  const [userConfig, setUserConfig] = useState(null);
  const [shortsData, setShortsData] = useState(null);

  // Handle when user clicks "Start Fetching" on homepage
  const handleStartFetching = async (config) => {
    console.log('📋 User Configuration:', config);
    
    // Save the config
    setUserConfig(config);
    
    // Hide homepage (this will show loading screen)
    setShowHomePage(false);

    // Immediately start loading data
    try {
      console.log('🔄 Loading data from API with user config:', config);
      const response = await fetch('http://localhost:3001/api/videos', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          topics: config.topics || [],
          custom_slang: config.customSlang || [],
          shorts_per_topic: config.shortsPerTopic || 10,
          comments_per_short: config.commentsPerShort || 50
        })
      });
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      const data = await response.json();
      console.log('✅ Loaded data from API:', data);
      setShortsData(data);
    } catch (err) {
      console.error('❌ Could not load data from API:', err);
      alert('Could not connect to backend API. Make sure the backend is running on port 3001!');
      // Go back to homepage on error
      setShowHomePage(true);
      setUserConfig(null);
    }
  };

  // Show homepage
  if (showHomePage) {
    return <HomePage onStartFetching={handleStartFetching} />;
  }

  // Show loading screen while fetching
  if (userConfig && !shortsData) {
    return (
      <div className="min-h-screen w-full bg-black flex items-center justify-center p-4">
        <div className="text-center">
          {/* Animated loading spinner */}
          <div className="relative inline-block mb-6">
            <div className="w-20 h-20 border-4 border-purple-600/30 border-t-purple-600 rounded-full animate-spin"></div>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-3xl">🎬</span>
            </div>
          </div>
          
          {/* Loading text */}
          <h2 className="text-white text-2xl font-bold mb-3">
            Fetching Videos...
          </h2>
          <p className="text-gray-400 text-sm mb-6">
            Loading {userConfig.topics.join(', ')} videos with slang comments
          </p>
          
          {/* Progress dots animation */}
          <div className="flex justify-center gap-2">
            <div className="w-3 h-3 bg-purple-600 rounded-full animate-pulse"></div>
            <div className="w-3 h-3 bg-purple-600 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
            <div className="w-3 h-3 bg-purple-600 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
          </div>
        </div>
      </div>
    );
  }

  // Show videos
  if (shortsData) {
    return (
      <div className="relative">
        {/* Original TikTok Component */}
        <BrainrotTikTok shortsData={shortsData} />
        
        {/* NEW: Add the refresh button */}
        <RefreshSlangButton 
          topics={userConfig?.topics || ['gaming', 'food review', 'dance']}
          apiUrl="http://localhost:3001"
          position="bottom-right"
          onSuccess={(newSlang) => {
            console.log('🎉 Discovered new slang!', newSlang);
            // Optionally reload data here
          }}
        />
      </div>
    );
  }

  return null;
}

export default App;