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
      </div>
    );
  }

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
