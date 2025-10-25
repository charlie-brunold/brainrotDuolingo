<<<<<<< Updated upstream
// src/App.js
import React, { useState, useEffect } from 'react';
import BrainrotTikTok from './Brainrottiktok';
import './App.css';

function App() {
  const [shortsData, setShortsData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Replace the URL with your backend endpoint
    fetch('http://localhost:3001/api/videos')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
        return res.json();
      })
      .then((data) => {
        setShortsData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error fetching videos:', err);
        setError('Failed to load videos. Is the backend running?');
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="h-screen w-full flex items-center justify-center bg-black text-white">
        Loading videos...
=======
import React, { useState } from 'react';
import HomePage from './Homepage';
import BrainrotTikTok from './Brainrottiktok.jsx';

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

  // Handle when user has run Python and wants to load the JSON
  const handleLoadData = () => {
    // Import the JSON file that Python created
    import('./youtube_shorts_slang_data.json')
      .then(data => {
        setShortsData(data.default);
      })
      .catch(err => {
        console.error('❌ Could not load JSON file:', err);
        alert('Could not find youtube_shorts_slang_data.json. Make sure you ran the Python script first!');
      });
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
            📋 Step 2: Run Python Script
          </h1>
          
          <div className="space-y-6">
            {/* User's Config */}
            <div className="bg-gray-800 rounded-lg p-4">
              <h2 className="text-white font-bold mb-3">Your Configuration:</h2>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Topics:</span>
                  <span className="text-white">{userConfig.topics.join(', ')}</span>
                </div>
                {userConfig.customSlang.length > 0 && (
                  <div className="flex justify-between">
                    <span className="text-gray-400">Custom Slang:</span>
                    <span className="text-white">{userConfig.customSlang.join(', ')}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-gray-400">Shorts per Topic:</span>
                  <span className="text-white">{userConfig.shortsPerTopic}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Comments per Short:</span>
                  <span className="text-white">{userConfig.commentsPerShort}</span>
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
                    <div className="font-semibold text-white">Open Terminal/Command Prompt</div>
                    <div className="text-gray-400 text-xs mt-1">Navigate to your project folder</div>
                  </div>
                </li>
                <li className="flex gap-3">
                  <span className="text-purple-400 font-bold">2.</span>
                  <div>
                    <div className="font-semibold text-white">Run the Python script:</div>
                    <code className="block bg-black text-green-400 px-3 py-2 rounded mt-2 text-xs">
                      python fetching.py
                    </code>
                  </div>
                </li>
                <li className="flex gap-3">
                  <span className="text-purple-400 font-bold">3.</span>
                  <div>
                    <div className="font-semibold text-white">Enter your settings when prompted:</div>
                    <div className="bg-black text-gray-300 px-3 py-2 rounded mt-2 text-xs space-y-1">
                      <div>Topics: <span className="text-yellow-400">{userConfig.topics.join(', ')}</span></div>
                      {userConfig.customSlang.length > 0 && (
                        <div>Custom slang: <span className="text-yellow-400">{userConfig.customSlang.join(', ')}</span></div>
                      )}
                      <div>Shorts per topic: <span className="text-yellow-400">{userConfig.shortsPerTopic}</span></div>
                      <div>Comments per short: <span className="text-yellow-400">{userConfig.commentsPerShort}</span></div>
                    </div>
                  </div>
                </li>
                <li className="flex gap-3">
                  <span className="text-purple-400 font-bold">4.</span>
                  <div>
                    <div className="font-semibold text-white">Wait for it to finish</div>
                    <div className="text-gray-400 text-xs mt-1">It will create youtube_shorts_slang_data.json</div>
                  </div>
                </li>
                <li className="flex gap-3">
                  <span className="text-purple-400 font-bold">5.</span>
                  <div>
                    <div className="font-semibold text-white">Click "Load Videos" button below</div>
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
>>>>>>> Stashed changes
      </div>
    );
  }

<<<<<<< Updated upstream
  if (error) {
    return (
      <div className="h-screen w-full flex items-center justify-center bg-black text-red-500">
        {error}
      </div>
    );
  }

  return (
    <div className="App">
      <BrainrotTikTok shortsData={shortsData} />
    </div>
  );
}

export default App;
=======
  // Show videos
  if (shortsData) {
    return <BrainrotTikTok shortsData={shortsData} />;
  }

  return null;
}

export default App;
>>>>>>> Stashed changes
