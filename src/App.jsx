// src/App.jsx
import React, { useState } from 'react';
import shortsData from './youtube_shorts_slang_data.json';

function App() {
  const [currentIndex, setCurrentIndex] = useState(0);

  const currentShort = shortsData[currentIndex];

  // ✅ Extract video ID from the YouTube URL (supports normal and shorts links)
  const extractVideoId = (url) => {
    const match = url.match(/(?:v=|\/shorts\/)([a-zA-Z0-9_-]{11})/);
    return match ? match[1] : null;
  };

  const videoId = extractVideoId(currentShort.url);

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto', padding: '20px' }}>
      {/* Video Section */}
      <div className="video-container" style={{ marginBottom: '20px' }}>
        {videoId ? (
          <iframe
            width="100%"
            height="400"
            src={`https://www.youtube.com/embed/${videoId}`}
            title={currentShort.title}
            frameBorder="0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
            allowFullScreen
            style={{ borderRadius: '8px' }}
          ></iframe>
        ) : (
          <img
            src={currentShort.thumbnail}
            alt={currentShort.title}
            style={{ width: '100%', borderRadius: '8px' }}
          />
        )}

        <h1>{currentShort.title}</h1>
        <p>By {currentShort.channel}</p>
        <p>
          {currentShort.view_count.toLocaleString()} views •{' '}
          {currentShort.like_count.toLocaleString()} likes
        </p>
      </div>

      {/* Slang Terms */}
      <div style={{ marginBottom: '20px' }}>
        <h3>Slang Terms Found:</h3>
        <div>
          {currentShort.unique_slang_terms.map((slang, idx) => (
            <span
              key={idx}
              style={{
                display: 'inline-block',
                padding: '5px 10px',
                margin: '5px',
                backgroundColor: '#e0e0e0',
                borderRadius: '15px',
              }}
            >
              {slang}
            </span>
          ))}
        </div>
      </div>

      {/* Comments */}
      <div style={{ marginBottom: '20px' }}>
        <h3>Comments with Slang:</h3>
        {currentShort.comments_with_slang.map((comment, idx) => (
          <div
            key={idx}
            style={{
              padding: '10px',
              marginBottom: '10px',
              backgroundColor: '#f5f5f5',
              borderRadius: '4px',
            }}
          >
            <strong>{comment.author}:</strong>
            <p>{comment.text}</p>
            <small>Contains: {comment.detected_slang.join(', ')}</small>
          </div>
        ))}
      </div>

      {/* Navigation */}
      <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
        <button
          onClick={() => setCurrentIndex((prev) => prev - 1)}
          disabled={currentIndex === 0}
          style={{ padding: '10px 20px' }}
        >
          ← Previous
        </button>
        <span style={{ padding: '10px' }}>
          {currentIndex + 1} / {shortsData.length}
        </span>
        <button
          onClick={() => setCurrentIndex((prev) => prev + 1)}
          disabled={currentIndex === shortsData.length - 1}
          style={{ padding: '10px 20px' }}
        >
          Next →
        </button>
      </div>
    </div>
  );
}

export default App;
