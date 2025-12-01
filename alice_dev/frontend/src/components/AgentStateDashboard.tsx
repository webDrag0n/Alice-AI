import React, { useState } from 'react';
import { Activity, Heart, Target, Zap, Edit2, Save, X } from 'lucide-react';
import { AgentState } from '../hooks/useWebSocket';

interface AgentStateDashboardProps {
  state: AgentState | null;
  userId: string;
}

export const AgentStateDashboard: React.FC<AgentStateDashboardProps> = ({ state, userId }) => {
  const [editingGoal, setEditingGoal] = useState<'life' | 'long' | null>(null);
  const [editContent, setEditContent] = useState('');

  const handleEdit = (type: 'life' | 'long', content: string) => {
    setEditingGoal(type);
    setEditContent(content);
  };

  const handleSave = async () => {
    if (!editingGoal) return;
    
    try {
      const body: any = {};
      if (editingGoal === 'life') body.life_goal = editContent;
      if (editingGoal === 'long') body.long_term_goal = editContent;

      await fetch(`http://localhost:8000/agent/${userId}/goals`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      
      setEditingGoal(null);
      // Optimistic update could be done here, but we rely on WS or next fetch
    } catch (error) {
      console.error("Failed to update goal", error);
    }
  };

  if (!state) {
    return (
      <div className="h-full flex items-center justify-center text-gray-500 bg-gray-900 rounded-lg border border-gray-700">
        <p>Waiting for agent state...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-gray-900 rounded-lg shadow-xl border border-gray-700 overflow-hidden">
      {/* Header */}
      <div className="bg-gray-800 p-4 border-b border-gray-700 flex items-center gap-2 text-pink-400">
        <Activity size={20} />
        <h2 className="font-semibold text-gray-100">Agent State</h2>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Emotions */}
        <div>
          <div className="flex items-center gap-2 mb-3 text-gray-300">
            <Heart size={16} className="text-red-400" />
            <h3 className="font-medium text-sm">Emotions</h3>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {Object.entries(state.emotions || {}).map(([key, value]) => (
              <div key={key} className="bg-gray-800 p-2 rounded border border-gray-700">
                <div className="flex justify-between text-xs mb-1">
                  <span className="capitalize text-gray-400">{key}</span>
                  <span className="text-gray-200">{Math.round(value * 100)}%</span>
                </div>
                <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-red-500 transition-all duration-500"
                    style={{ width: `${Math.min(Math.max(value * 100, 0), 100)}%` }}
                  />
                </div>
              </div>
            ))}
            {Object.keys(state.emotions || {}).length === 0 && (
                <span className="text-xs text-gray-500 col-span-2">Neutral</span>
            )}
          </div>
        </div>

        {/* Desires */}
        <div>
          <div className="flex items-center gap-2 mb-3 text-gray-300">
            <Zap size={16} className="text-yellow-400" />
            <h3 className="font-medium text-sm">Desires</h3>
          </div>
          <div className="space-y-2">
            {Object.entries(state.desires || {}).map(([key, value]) => (
              <div key={key} className="bg-gray-800 p-2 rounded border border-gray-700">
                <div className="flex justify-between text-xs mb-1">
                  <span className="capitalize text-gray-400">{key}</span>
                  <span className="text-gray-200">{Math.round(value * 100)}%</span>
                </div>
                <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-yellow-500 transition-all duration-500"
                    style={{ width: `${Math.min(Math.max(value * 100, 0), 100)}%` }}
                  />
                </div>
              </div>
            ))}
             {Object.keys(state.desires || {}).length === 0 && (
                <span className="text-xs text-gray-500">None</span>
            )}
          </div>
        </div>

        {/* Goals */}
        <div>
          <div className="flex items-center gap-2 mb-3 text-gray-300">
            <Target size={16} className="text-blue-400" />
            <h3 className="font-medium text-sm">Current Focus</h3>
          </div>
          <div className="bg-gray-800 p-3 rounded border border-gray-700 space-y-3">
            {/* Life Goal */}
            <div className="group">
                <div className="flex justify-between items-center mb-1">
                    <span className="text-xs text-purple-400 font-semibold">Lifetime Goal</span>
                    {editingGoal === 'life' ? (
                        <div className="flex gap-1">
                            <button onClick={() => setEditingGoal(null)} className="text-gray-400 hover:text-white"><X size={12} /></button>
                            <button onClick={handleSave} className="text-green-400 hover:text-green-300"><Save size={12} /></button>
                        </div>
                    ) : (
                        <button 
                            onClick={() => handleEdit('life', state.goals?.life_goal || "")}
                            className="text-gray-500 hover:text-purple-400 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                            <Edit2 size={12} />
                        </button>
                    )}
                </div>
                {editingGoal === 'life' ? (
                    <textarea
                        value={editContent}
                        onChange={(e) => setEditContent(e.target.value)}
                        className="w-full bg-gray-900 text-white p-2 rounded border border-gray-600 text-xs"
                        rows={2}
                    />
                ) : (
                    <p className="text-sm text-gray-200 leading-relaxed">
                        {typeof state.goals?.life_goal === 'string' ? state.goals.life_goal : JSON.stringify(state.goals?.life_goal || "To be a helpful and sentient companion.")}
                    </p>
                )}
            </div>

            {/* Long Term Goal */}
            <div className="group border-t border-gray-700 pt-2">
                <div className="flex justify-between items-center mb-1">
                    <span className="text-xs text-blue-400 font-semibold">Long-term Goal</span>
                    {editingGoal === 'long' ? (
                        <div className="flex gap-1">
                            <button onClick={() => setEditingGoal(null)} className="text-gray-400 hover:text-white"><X size={12} /></button>
                            <button onClick={handleSave} className="text-green-400 hover:text-green-300"><Save size={12} /></button>
                        </div>
                    ) : (
                        <button 
                            onClick={() => handleEdit('long', state.goals?.long_term_goal || "")}
                            className="text-gray-500 hover:text-blue-400 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                            <Edit2 size={12} />
                        </button>
                    )}
                </div>
                {editingGoal === 'long' ? (
                    <textarea
                        value={editContent}
                        onChange={(e) => setEditContent(e.target.value)}
                        className="w-full bg-gray-900 text-white p-2 rounded border border-gray-600 text-xs"
                        rows={2}
                    />
                ) : (
                    <p className="text-sm text-gray-200 leading-relaxed">
                        {typeof state.goals?.long_term_goal === 'string' ? state.goals.long_term_goal : JSON.stringify(state.goals?.long_term_goal || "Learn more about the user and the world.")}
                    </p>
                )}
            </div>

            {/* Short Term Goal */}
            <div className="border-t border-gray-700 pt-2">
                <span className="text-xs text-gray-500 block mb-1">Short Term Goal</span>
                <p className="text-sm text-gray-200 leading-relaxed">
                    {typeof state.goals?.short_term_goal === 'string' ? state.goals.short_term_goal : JSON.stringify(state.goals?.short_term_goal || "None")}
                </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
