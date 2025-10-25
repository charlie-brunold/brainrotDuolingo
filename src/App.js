// src/App.js
import React, { useState } from "react";
import shortsData from "./youtube_shorts_slang_data.json";

function App() {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [userComment, setUserComment] = useState("");
  const [evaluation, setEvaluation] = useState(null);

  const currentShort = shortsData[currentIndex];

  // Extract YouTube video ID (works for normal URLs and shorts)
  const extractVideoId = (url) => {
    const match = url.match(/(?:v=|\/shorts\/)([a-zA-Z0-9_-]{11})/);
    return match ? match[1] : null;
  };

  const videoId = extractVideoId(currentShort.url);

  // Send user comment to backend for AI evaluation
  const handleEvaluate = async () => {
    try {
      const res = await fetch("http://localhost:3001/api/evaluate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          videoTitle: currentShort.title,
          videoDescription: currentShort.description || "",
          userComment,
          targetLanguage: "English",
        }),
      });
      const data = await res.json();
      setEvaluation(data);
    } catch (err) {
      console.error("Error evaluating comment:", err);
    }
  };

  return (
    <div style={{ maxWidth: "600px", margin: "0 auto", padding: "20px" }}>
      {/* Video Section */}
      <div style={{ marginBottom: "20px" }}>
        {videoId ? (
          <iframe
            width="100%"
            height="400"
            src={`https://www.youtube.com/embed/${videoId}`}
            title={currentShort.title}
            frameBorder="0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
            allowFullScreen
            style={{ borderRadius: "8px" }}
          ></iframe>
        ) : (
          <img
            src={currentShort.thumbnail}
            alt={currentShort.title}
            style={{ width: "100%", borderRadius: "8px" }}
          />
        )}

        <h1>{currentShort.title}</h1>
        <p>By {currentShort.channel}</p>
        <p>
          {currentShort.view_count.toLocaleString()} views •{" "}
          {currentShort.like_count.toLocaleString()} likes
        </p>
      </div>

      {/* Slang Terms */}
      <div style={{ marginBottom: "20px" }}>
        <h3>Slang Terms Found:</h3>
        <div>
          {currentShort.unique_slang_terms.map((slang, idx) => (
            <span
              key={idx}
              style={{
                display: "inline-block",
                padding: "5px 10px",
                margin: "5px",
                backgroundColor: "#e0e0e0",
                borderRadius: "15px",
              }}
            >
              {slang}
            </span>
          ))}
        </div>
      </div>

      {/* Comments */}
      <div style={{ marginBottom: "20px" }}>
        <h3>Comments with Slang:</h3>
        {currentShort.comments_with_slang.map((comment, idx) => (
          <div
            key={idx}
            style={{
              padding: "10px",
              marginBottom: "10px",
              backgroundColor: "#f5f5f5",
              borderRadius: "4px",
            }}
          >
            <strong>{comment.author}:</strong>
            <p>{comment.text}</p>
            <small>Contains: {comment.detected_slang.join(", ")}</small>
          </div>
        ))}
      </div>

      {/* User Comment Evaluation */}
      <div style={{ marginBottom: "20px" }}>
        <h3>Try Your Comment:</h3>
        <input
          type="text"
          value={userComment}
          onChange={(e) => setUserComment(e.target.value)}
          placeholder="Enter your comment"
          style={{ width: "80%", padding: "8px" }}
        />
        <button
          onClick={handleEvaluate}
          style={{ padding: "8px 12px", marginLeft: "10px" }}
        >
          Evaluate
        </button>

        {evaluation && (
          <div
            style={{
              marginTop: "10px",
              backgroundColor: "#eef",
              padding: "10px",
              borderRadius: "5px",
            }}
          >
            <p>Grammar: {evaluation.grammarScore}</p>
            <p>Context: {evaluation.contextScore}</p>
            <p>Naturalness: {evaluation.naturalnessScore}</p>
            <p>Correction: {evaluation.correction}</p>
            <p>Mistakes: {evaluation.mistakes.join(", ")}</p>
            <p>Good parts: {evaluation.goodParts.join(", ")}</p>
          </div>
        )}
      </div>

      {/* Navigation */}
      <div style={{ display: "flex", gap: "10px", justifyContent: "center" }}>
        <button
          onClick={() => setCurrentIndex((prev) => prev - 1)}
          disabled={currentIndex === 0}
          style={{ padding: "10px 20px" }}
        >
          ← Previous
        </button>
        <span style={{ padding: "10px" }}>
          {currentIndex + 1} / {shortsData.length}
        </span>
        <button
          onClick={() => setCurrentIndex((prev) => prev + 1)}
          disabled={currentIndex === shortsData.length - 1}
          style={{ padding: "10px 20px" }}
        >
          Next →
        </button>
      </div>
    </div>
  );
}

export default App;
