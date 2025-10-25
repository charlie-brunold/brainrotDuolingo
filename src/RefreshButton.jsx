import React, { useState, useEffect } from 'react';
import { Sparkles, RefreshCw, X } from 'lucide-react';

/**
 * Standalone Refresh Slang Button Component
 * 
 * Usage in your main app:
 * import RefreshSlangButton from './RefreshSlangButton';
 * 
 * <RefreshSlangButton 
 *   topics={['gaming', 'food review']} 
 *   onSuccess={(newSlang) => console.log('New slang!', newSlang)}
 * />
 */

const RefreshSlangButton = ({ 
  topics = ['gaming', 'food review', 'funny moments', 'dance'],
  apiUrl = 'http://localhost:3001',
  onSuccess = null,
  position = 'bottom-right' // 'bottom-right', 'bottom-left', 'top-right', 'top-left'
}) => {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [slangCount, setSlangCount] = useState(0);
  const [newSlangDiscovered, setNewSlangDiscovered] = useState([]);
  const [showNotification, setShowNotification] = useState(false);
  const [error, setError] = useState(null);

  // Load current slang count on mount
  useEffect(() => {
    loadSlangCount();
  }, []);

  const loadSlangCount = async () => {
    try {
      const response = await fetch(`${apiUrl}/api/slang`);
      const data = await response.json();
      setSlangCount(data.total_terms || 0);
    } catch (err) {
      console.error('Error loading slang count:', err);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    setError(null);
    setNewSlangDiscovered([]);
    setShowNotification(false);

    try {
      const response = await fetch(`${apiUrl}/api/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topics })
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      const data = await response.json();
      
      // Update slang count
      setSlangCount(data.total_slang_terms || 0);

      // Check for new slang
      if (data.new_slang_discovered && data.new_slang_discovered.length > 0) {
        setNewSlangDiscovered(data.new_slang_discovered);
        setShowNotification(true);
        
        // Auto-hide after 8 seconds
        setTimeout(() => setShowNotification(false), 8000);

        // Call success callback if provided
        if (onSuccess) {
          onSuccess(data.new_slang_discovered);
        }
      } else {
        // Show brief success message even if no new slang
        setShowNotification(true);
        setTimeout(() => setShowNotification(false), 3000);
      }

    } catch (err) {
      console.error('Refresh error:', err);
      setError(err.message);
      setTimeout(() => setError(null), 5000);
    } finally {
      setIsRefreshing(false);
    }
  };

  // Position styles
  const positions = {
    'bottom-right': 'bottom-20 right-4',
    'bottom-left': 'bottom-20 left-4',
    'top-right': 'top-20 right-4',
    'top-left': 'top-20 left-4'
  };

  const notificationPositions = {
    'bottom-right': 'bottom-32 right-4',
    'bottom-left': 'bottom-32 left-4',
    'top-right': 'top-32 right-4',
    'top-left': 'top-32 left-4'
  };

  return (
    <>
      {/* Main Button */}
      <button
        onClick={handleRefresh}
        disabled={isRefreshing}
        className={`fixed ${positions[position]} z-50 group`}
        style={{
          background: isRefreshing 
            ? 'linear-gradient(135deg, #6b7280 0%, #4b5563 100%)'
            : 'linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%)',
          padding: '12px',
          borderRadius: '50%',
          border: 'none',
          cursor: isRefreshing ? 'not-allowed' : 'pointer',
          boxShadow: '0 4px 12px rgba(139, 92, 246, 0.4)',
          transition: 'all 0.3s ease',
          width: '56px',
          height: '56px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}
        onMouseEnter={(e) => {
          if (!isRefreshing) {
            e.currentTarget.style.transform = 'scale(1.1)';
            e.currentTarget.style.boxShadow = '0 6px 20px rgba(139, 92, 246, 0.6)';
          }
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'scale(1)';
          e.currentTarget.style.boxShadow = '0 4px 12px rgba(139, 92, 246, 0.4)';
        }}
      >
        {isRefreshing ? (
          <RefreshCw 
            className="animate-spin" 
            style={{ width: '24px', height: '24px', color: 'white' }} 
          />
        ) : (
          <Sparkles style={{ width: '24px', height: '24px', color: 'white' }} />
        )}
        
        {/* Tooltip */}
        <div
          className="absolute opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none"
          style={{
            bottom: '100%',
            right: '0',
            marginBottom: '8px',
            background: '#1f2937',
            color: 'white',
            padding: '6px 12px',
            borderRadius: '6px',
            fontSize: '12px',
            fontWeight: '600',
            whiteSpace: 'nowrap',
            boxShadow: '0 2px 8px rgba(0,0,0,0.2)'
          }}
        >
          {isRefreshing 
            ? 'Discovering...' 
            : `Discover New Slang (${slangCount})`
          }
        </div>
      </button>

      {/* Success Notification */}
      {showNotification && newSlangDiscovered.length > 0 && (
        <div
          className={`fixed ${notificationPositions[position]} z-50`}
          style={{
            maxWidth: '320px',
            animation: 'slideIn 0.3s ease-out'
          }}
        >
          <div
            style={{
              background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
              borderRadius: '12px',
              padding: '16px',
              boxShadow: '0 8px 24px rgba(16, 185, 129, 0.4)',
              color: 'white'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'start', gap: '12px' }}>
              <Sparkles style={{ width: '24px', height: '24px', flexShrink: 0, marginTop: '2px' }} />
              
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 'bold', fontSize: '16px', marginBottom: '8px' }}>
                  🎉 Found {newSlangDiscovered.length} New Slang!
                </div>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {newSlangDiscovered.slice(0, 3).map((slang, idx) => (
                    <div
                      key={idx}
                      style={{
                        background: 'rgba(255, 255, 255, 0.2)',
                        borderRadius: '6px',
                        padding: '8px',
                        fontSize: '13px'
                      }}
                    >
                      <div style={{ fontWeight: 'bold', marginBottom: '2px' }}>
                        {slang.term}
                      </div>
                      <div style={{ fontSize: '12px', opacity: 0.9 }}>
                        {slang.definition}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <button
                onClick={() => setShowNotification(false)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'white',
                  cursor: 'pointer',
                  padding: '4px',
                  opacity: 0.7,
                  transition: 'opacity 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
                onMouseLeave={(e) => e.currentTarget.style.opacity = '0.7'}
              >
                <X style={{ width: '20px', height: '20px' }} />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* No New Slang Notification */}
      {showNotification && newSlangDiscovered.length === 0 && (
        <div
          className={`fixed ${notificationPositions[position]} z-50`}
          style={{
            maxWidth: '280px',
            animation: 'slideIn 0.3s ease-out'
          }}
        >
          <div
            style={{
              background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
              borderRadius: '12px',
              padding: '12px 16px',
              boxShadow: '0 8px 24px rgba(59, 130, 246, 0.4)',
              color: 'white',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            <span style={{ fontSize: '16px' }}>✓</span>
            <span style={{ fontSize: '14px', fontWeight: '600' }}>
              No new slang found this time
            </span>
          </div>
        </div>
      )}

      {/* Error Notification */}
      {error && (
        <div
          className={`fixed ${notificationPositions[position]} z-50`}
          style={{
            maxWidth: '280px',
            animation: 'slideIn 0.3s ease-out'
          }}
        >
          <div
            style={{
              background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
              borderRadius: '12px',
              padding: '12px 16px',
              boxShadow: '0 8px 24px rgba(239, 68, 68, 0.4)',
              color: 'white',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            <span style={{ fontSize: '16px' }}>⚠️</span>
            <span style={{ fontSize: '14px', fontWeight: '600' }}>
              {error}
            </span>
          </div>
        </div>
      )}

      {/* Add slide-in animation */}
      <style>{`
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </>
  );
};

export default RefreshSlangButton;