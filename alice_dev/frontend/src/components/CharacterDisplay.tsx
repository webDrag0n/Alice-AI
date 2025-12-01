import React from 'react';
import { VisualState } from '../hooks/useWebSocket';

interface CharacterDisplayProps {
  visualState: VisualState;
  backgroundColor?: string;
}

export const CharacterDisplay: React.FC<CharacterDisplayProps> = ({ visualState, backgroundColor = 'bg-gray-900' }) => {
  const { body, face } = visualState;
  
  // Construct image path
  // Naming convention: alice_{body}_{face}.png
  // Example: alice_idle_neutral.png
  const imagePath = `/character_images/alice_${body}_${face}.png`;

  return (
    <div className={`${backgroundColor} transition-colors duration-1000 rounded-lg p-4 h-full flex flex-col items-center justify-center border border-gray-800 shadow-lg relative overflow-hidden`}>
      <div className="absolute inset-0 bg-gradient-to-b from-transparent to-gray-900/50 pointer-events-none" />
      
      {/* Character Image */}
      <div className="relative w-full h-full flex items-center justify-center">
        <img 
          src={imagePath} 
          alt={`Alice ${body} ${face}`}
          className="max-h-full max-w-full object-contain transition-opacity duration-500"
          onError={(e) => {
            // Fallback to idle_neutral if image not found
            const target = e.target as HTMLImageElement;
            if (target.src.indexOf('alice_idle_neutral.png') === -1) {
                target.src = '/character_images/alice_idle_neutral.png';
            }
          }}
        />
      </div>

      {/* Status Label */}
      <div className="absolute bottom-4 left-4 bg-black/60 backdrop-blur-sm px-3 py-1 rounded-full text-xs text-gray-300 border border-gray-700">
        {body} • {face}
      </div>
    </div>
  );
};
