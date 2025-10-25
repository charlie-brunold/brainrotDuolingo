import React, { useState } from 'react';
import HomePage from './Homepage';
import BrainrotTikTok from './Brainrottiktok.jsx';
import RefreshSlangButton from './RefreshButton.jsx';
function App() {
  const [showHomePage, setShowHomePage] = useState(true);
  const [userConfig, setUserConfig] = useState(null);
  const [shortsData, setShortsData] = useState(null);

  // Handle when user clicks "Start Fetching" on homepage
  const handleStartFetching = (config) => {
    console.log('📋 User Configuration:', config);
    
    // Save the config
    setUserConfig(config);
    
    // Hide homepage and show instructions
    setShowHomePage(false);
  };

  // Handle when user wants to load data from API
  const handleLoadData = async () => {
    try {
      console.log('🔄 Loading data from API with user config:', userConfig);
      const response = await fetch('http://localhost:3001/api/videos', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          topics: userConfig.topics || [],
          custom_slang: userConfig.custom_slang || [],
          shorts_per_topic: userConfig.shorts_per_topic || 10,
          comments_per_short: userConfig.comments_per_short || 50
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
    }
  };

  // Show homepage
  if (showHomePage) {
    return <HomePage onStartFetching={handleStartFetching} />;
  }

  // Show instructions to run Python
  if (userConfig && !shortsData) {
    return (
      <div className="min-h-screen w-full bg-black flex items-center justify-center p-4">
        <div className="max-w-2xl w-full bg-gray-900 rounded-2xl p-8">
          <h1 className="text-3xl font-bold text-white mb-6 text-center">
            📋 Step 2: Load Videos from API
          </h1>
          
          <div className="space-y-6">
            {/* User's Config */}
            <div className="bg-gray-800 rounded-lg p-4">
              <h2 className="text-white font-bold mb-3">Your Configuration:</h2>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Topics:</span>
                  <span className="text-white">{userConfig.topics ? userConfig.topics.join(', ') : 'None'}</span>
                </div>
                {userConfig.custom_slang && userConfig.custom_slang.length > 0 && (
                  <div className="flex justify-between">
                    <span className="text-gray-400">Custom Slang:</span>
                    <span className="text-white">{userConfig.custom_slang.join(', ')}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-gray-400">Shorts per Topic:</span>
                  <span className="text-white">{userConfig.shorts_per_topic}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Comments per Short:</span>
                  <span className="text-white">{userConfig.comments_per_short}</span>
                </div>
              </div>
            </div>

            {/* Instructions */}
            <div className="bg-purple-900/30 border border-purple-500 rounded-lg p-4">
              <h2 className="text-white font-bold mb-3">Instructions:</h2>
              <ol className="space-y-3 text-gray-300 text-sm">
                <li className="flex gap-3">
                  <span className="text-purple-400 font-bold">1.</span>
                  <div>
                    <div className="font-semibold text-white">Make sure backend is running</div>
                    <div className="text-gray-400 text-xs mt-1">Backend should be running on port 3001</div>
                  </div>
                </li>
                <li className="flex gap-3">
                  <span className="text-purple-400 font-bold">2.</span>
                  <div>
                    <div className="font-semibold text-white">Click "Load Videos" button below</div>
                    <div className="text-gray-400 text-xs mt-1">This will fetch videos from the API using your configuration</div>
                  </div>
                </li>
                <li className="flex gap-3">
                  <span className="text-purple-400 font-bold">3.</span>
                  <div>
                    <div className="font-semibold text-white">Start scrolling through videos!</div>
                    <div className="text-gray-400 text-xs mt-1">Use mouse wheel or swipe to navigate between videos</div>
                  </div>
                </li>
              </ol>
            </div>

            {/* Buttons */}
            <div className="flex gap-3">
              <button
                onClick={() => setShowHomePage(true)}
                className="flex-1 bg-gray-700 text-white rounded-lg px-6 py-3 font-semibold hover:bg-gray-600"
              >
                ← Back to Config
              </button>
              <button
                onClick={handleLoadData}
                className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg px-6 py-3 font-semibold hover:opacity-90"
              >
                Load Videos →
              </button>
            </div>

            {/* Tip */}
            <div className="text-center text-gray-500 text-xs">
              💡 Tip: Keep this page open while running the Python script
            </div>
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
