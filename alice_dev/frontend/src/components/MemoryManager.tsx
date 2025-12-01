import React, { useState, useEffect } from 'react';
import { Search, Plus, Trash2, Edit2, Save, X, Brain, Heart, Lightbulb, Zap, Sparkles } from 'lucide-react';

interface Memory {
  id: string;
  content: string;
  type: string;
  timestamp: string;
  importance: number;
  distance?: number;
  tags?: string[];
}

interface SocialState {
  intimacy: number;
  trust: number;
  stage: string;
  summary: string;
}

interface Action {
  name: string;
  description: string;
  parameters: Record<string, string>;
  category: string;
}

interface Metacognition {
    id: string;
    type: string;
    content: string;
}

import { AgentState } from '../hooks/useWebSocket';

interface MemoryManagerProps {
  userId: string;
  agentState: AgentState | null;
}

export const MemoryManager: React.FC<MemoryManagerProps> = ({ userId, agentState }) => {
  const [activeTab, setActiveTab] = useState<'episodic' | 'cognitive' | 'social' | 'actions' | 'metacognition' | 'instant'>('episodic');
  const [memories, setMemories] = useState<Memory[]>([]);
  const [socialState, setSocialState] = useState<SocialState | null>(null);
  const [actions, setActions] = useState<Action[]>([]);
  const [metacognition, setMetacognition] = useState<Metacognition[]>([]);
  const [selectedAction, setSelectedAction] = useState<Action | null>(null);
  const [query, setQuery] = useState('');
  const [isAdding, setIsAdding] = useState(false);
  const [newContent, setNewContent] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');

  const fetchMemories = async () => {
    try {
      let url = `http://localhost:8000/memories/?user_id=${userId}`;
      if (activeTab !== 'social' && activeTab !== 'actions' && activeTab !== 'metacognition') {
          url += `&type=${activeTab}`;
      }
      if (query) {
        url += `&query=${encodeURIComponent(query)}`;
      }
      
      const res = await fetch(url);
      const data = await res.json();
      setMemories(data);
    } catch (error) {
      console.error("Failed to fetch memories", error);
    }
  };

  const fetchSocialState = async () => {
      try {
          const res = await fetch(`http://localhost:8000/memories/social_state/${userId}`);
          const data = await res.json();
          setSocialState(data);
      } catch (error) {
          console.error("Failed to fetch social state", error);
      }
  };

  const fetchActions = async () => {
    try {
        const res = await fetch(`http://localhost:8000/memories/actions?user_id=${userId}`);
        const data = await res.json();
        setActions(data);
    } catch (error) {
        console.error("Failed to fetch actions", error);
    }
  };

  const fetchMetacognition = async () => {
      try {
          const res = await fetch(`http://localhost:8000/memories/metacognition`);
          const data = await res.json();
          setMetacognition(data);
      } catch (error) {
          console.error("Failed to fetch metacognition", error);
      }
  };

  useEffect(() => {
    if (activeTab === 'social') {
        fetchSocialState();
    } else if (activeTab === 'actions') {
        fetchActions();
    } else if (activeTab === 'metacognition') {
        fetchMetacognition();
    } else if (activeTab === 'instant') {
        // Data comes from props (agentState), no fetch needed
    } else {
        fetchMemories();
    }
  }, [userId, query, activeTab]);

  const handleAdd = async () => {
    if (!newContent.trim()) return;
    try {
      await fetch('http://localhost:8000/memories/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: newContent,
          user_id: userId,
          type: activeTab === 'cognitive' ? 'cognitive' : 'episodic',
          importance: 0.8
        })
      });
      setNewContent('');
      setIsAdding(false);
      fetchMemories();
    } catch (error) {
      console.error("Failed to add memory", error);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this memory?")) return;
    try {
      await fetch(`http://localhost:8000/memories/${id}`, {
        method: 'DELETE'
      });
      fetchMemories();
    } catch (error) {
      console.error("Failed to delete memory", error);
    }
  };

  const handleUpdate = async (id: string) => {
    try {
      await fetch(`http://localhost:8000/memories/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: editContent })
      });
      setEditingId(null);
      fetchMemories();
    } catch (error) {
      console.error("Failed to update memory", error);
    }
  };

  const renderSocialState = () => {
      if (!socialState) return <div className="p-4 text-gray-400">Loading social state...</div>;
      return (
          <div className="p-6 space-y-6">
              <div className="grid grid-cols-2 gap-4">
                  <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
                      <div className="text-gray-400 text-sm mb-1">Intimacy</div>
                      <div className="text-2xl font-bold text-pink-500">{socialState.intimacy}%</div>
                      <div className="w-full bg-gray-700 h-2 rounded-full mt-2">
                          <div className="bg-pink-500 h-2 rounded-full" style={{ width: `${socialState.intimacy}%` }}></div>
                      </div>
                  </div>
                  <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
                      <div className="text-gray-400 text-sm mb-1">Trust</div>
                      <div className="text-2xl font-bold text-blue-500">{socialState.trust}%</div>
                      <div className="w-full bg-gray-700 h-2 rounded-full mt-2">
                          <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${socialState.trust}%` }}></div>
                      </div>
                  </div>
              </div>
              
              <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
                  <div className="text-gray-400 text-sm mb-2">Relationship Stage</div>
                  <div className="text-xl font-semibold text-purple-400 capitalize">{socialState.stage}</div>
              </div>

              <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
                  <div className="text-gray-400 text-sm mb-2">Summary</div>
                  <p className="text-gray-300 italic">"{socialState.summary}"</p>
              </div>
          </div>
      );
  };

  const renderMetacognition = () => {
      return (
          <div className="p-4 space-y-4">
              {metacognition.map((meta) => (
                  <div key={meta.id} className="bg-gray-800 p-4 rounded-lg border border-gray-700 hover:border-purple-500/50 transition-colors">
                      <div className="flex items-center gap-2 mb-2">
                          <Sparkles size={16} className="text-purple-400" />
                          <span className="text-xs font-semibold text-purple-400 uppercase tracking-wider">{meta.type}</span>
                      </div>
                      <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">{meta.content}</p>
                  </div>
              ))}
          </div>
      );
  };

  const renderActions = () => {
    const grouped = actions.reduce((acc, action) => {
        const cat = action.category || 'general';
        if (!acc[cat]) acc[cat] = [];
        acc[cat].push(action);
        return acc;
    }, {} as Record<string, Action[]>);

    const categoryColors: Record<string, string> = {
        rest: 'bg-gray-700 text-gray-300 hover:bg-gray-600',
        memory: 'bg-blue-900/30 text-blue-300 border-blue-800/50 hover:bg-blue-900/50',
        learning: 'bg-green-900/30 text-green-300 border-green-800/50 hover:bg-green-900/50',
        coding: 'bg-purple-900/30 text-purple-300 border-purple-800/50 hover:bg-purple-900/50',
        expression: 'bg-pink-900/30 text-pink-300 border-pink-800/50 hover:bg-pink-900/50',
        social: 'bg-red-900/30 text-red-300 border-red-800/50 hover:bg-red-900/50',
        daily: 'bg-yellow-900/30 text-yellow-300 border-yellow-800/50 hover:bg-yellow-900/50',
        general: 'bg-gray-800 text-gray-300 border-gray-700 hover:bg-gray-700'
    };

    return (
        <div className="p-4 space-y-6">
            {Object.entries(grouped).map(([category, categoryActions]) => (
                <div key={category}>
                    <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 ml-1">{category}</h3>
                    <div className="grid grid-cols-2 gap-3">
                        {categoryActions.map(action => (
                            <button
                                key={action.name}
                                onClick={() => setSelectedAction(action)}
                                className={`p-3 rounded-lg border text-left transition-all hover:scale-105 ${categoryColors[category] || categoryColors.general}`}
                            >
                                <div className="font-medium text-sm mb-1 truncate">{action.name}</div>
                                <div className="text-xs opacity-70 truncate">{action.description}</div>
                            </button>
                        ))}
                    </div>
                </div>
            ))}
        </div>
    );
  };

  const renderInstantMemory = () => {
    const instantMemories = agentState?.instant_memory || [];
    if (instantMemories.length === 0) {
        return <div className="p-8 text-center text-gray-500 italic">No instant memories yet...</div>;
    }
    return (
        <div className="p-4 space-y-3">
            {instantMemories.map((mem, idx) => (
                <div key={idx} className="bg-gray-800/50 p-3 rounded border border-gray-700/50 text-gray-300 text-sm flex gap-3">
                    <span className="text-gray-500 font-mono text-xs pt-0.5">[{idx + 1}]</span>
                    <span>{mem}</span>
                </div>
            ))}
        </div>
    );
  };

  return (
    <div className="flex flex-col h-full bg-gray-900 rounded-lg shadow-xl border border-gray-700 overflow-hidden relative">
      {/* Header */}
      <div className="bg-gray-800 p-4 border-b border-gray-700 flex flex-col gap-4">
        <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-purple-400">
            <Brain size={20} />
            <h2 className="font-semibold text-gray-100">Memory Bank</h2>
            </div>
            {activeTab !== 'social' && activeTab !== 'actions' && activeTab !== 'metacognition' && activeTab !== 'instant' && (
                <button 
                onClick={() => setIsAdding(!isAdding)}
                className="p-1 hover:bg-gray-700 rounded text-gray-300 transition-colors"
                >
                <Plus size={20} />
                </button>
            )}
        </div>
        
        {/* Tabs */}
        <div className="flex gap-2 bg-gray-900 p-1 rounded-lg flex-wrap">
            <button 
                onClick={() => setActiveTab('instant')}
                className={`flex-1 py-1 px-3 rounded-md text-sm font-medium transition-colors flex items-center justify-center gap-2 whitespace-nowrap ${activeTab === 'instant' ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-gray-200'}`}
            >
                <Zap size={14} /> Instant
            </button>
            <button 
                onClick={() => setActiveTab('episodic')}
                className={`flex-1 py-1 px-3 rounded-md text-sm font-medium transition-colors flex items-center justify-center gap-2 whitespace-nowrap ${activeTab === 'episodic' ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-gray-200'}`}
            >
                <Brain size={14} /> Episodic
            </button>
            <button 
                onClick={() => setActiveTab('cognitive')}
                className={`flex-1 py-1 px-3 rounded-md text-sm font-medium transition-colors flex items-center justify-center gap-2 whitespace-nowrap ${activeTab === 'cognitive' ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-gray-200'}`}
            >
                <Lightbulb size={14} /> Beliefs
            </button>
            <button 
                onClick={() => setActiveTab('social')}
                className={`flex-1 py-1 px-3 rounded-md text-sm font-medium transition-colors flex items-center justify-center gap-2 whitespace-nowrap ${activeTab === 'social' ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-gray-200'}`}
            >
                <Heart size={14} /> Social
            </button>
            <button 
                onClick={() => setActiveTab('actions')}
                className={`flex-1 py-1 px-3 rounded-md text-sm font-medium transition-colors flex items-center justify-center gap-2 whitespace-nowrap ${activeTab === 'actions' ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-gray-200'}`}
            >
                <Zap size={14} /> Actions
            </button>
            <button 
                onClick={() => setActiveTab('metacognition')}
                className={`flex-1 py-1 px-3 rounded-md text-sm font-medium transition-colors flex items-center justify-center gap-2 whitespace-nowrap ${activeTab === 'metacognition' ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-gray-200'}`}
            >
                <Sparkles size={14} /> Meta
            </button>
        </div>

        {activeTab !== 'social' && activeTab !== 'actions' && activeTab !== 'metacognition' && activeTab !== 'instant' && (
            <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500" size={16} />
            <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={`Search ${activeTab} memories...`}
                className="w-full bg-gray-900 text-gray-200 pl-10 pr-4 py-2 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-purple-500 border border-gray-700"
            />
            </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'social' ? (
            renderSocialState()
        ) : activeTab === 'actions' ? (
            renderActions()
        ) : activeTab === 'metacognition' ? (
            renderMetacognition()
        ) : activeTab === 'instant' ? (
            renderInstantMemory()
        ) : (
            <>
                {isAdding && (
                <div className="p-4 border-b border-gray-700 bg-gray-800/50">
                    <textarea
                    value={newContent}
                    onChange={(e) => setNewContent(e.target.value)}
                    placeholder="Enter new memory content..."
                    className="w-full bg-gray-900 text-white p-3 rounded-lg border border-gray-600 focus:outline-none focus:border-purple-500 min-h-[80px] text-sm"
                    autoFocus
                    />
                    <div className="flex justify-end gap-2 mt-2">
                    <button 
                        onClick={() => setIsAdding(false)}
                        className="px-3 py-1 text-xs text-gray-400 hover:text-white"
                    >
                        Cancel
                    </button>
                    <button 
                        onClick={handleAdd}
                        className="px-3 py-1 text-xs bg-purple-600 text-white rounded hover:bg-purple-500 flex items-center gap-1"
                    >
                        <Save size={14} /> Save
                    </button>
                    </div>
                </div>
                )}

                <div className="p-4 space-y-3">
                {memories.map((memory) => (
                    <div key={memory.id} className="bg-gray-800 p-3 rounded-lg border border-gray-700 group hover:border-gray-600 transition-colors">
                    {editingId === memory.id ? (
                        <div className="space-y-2">
                        <textarea
                            value={editContent}
                            onChange={(e) => setEditContent(e.target.value)}
                            className="w-full bg-gray-900 text-white p-2 rounded border border-gray-600 text-sm"
                        />
                        <div className="flex justify-end gap-2">
                            <button onClick={() => setEditingId(null)} className="p-1 text-gray-400 hover:text-white"><X size={16} /></button>
                            <button onClick={() => handleUpdate(memory.id)} className="p-1 text-green-400 hover:text-green-300"><Save size={16} /></button>
                        </div>
                        </div>
                    ) : (
                        <>
                        <div className="flex justify-between items-start mb-2">
                            <span className={`text-xs px-2 py-0.5 rounded-full ${
                                memory.type === 'cognitive' ? 'bg-yellow-900/50 text-yellow-400' : 'bg-blue-900/50 text-blue-400'
                            }`}>
                            {memory.type}
                            </span>
                            <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button 
                                onClick={() => {
                                setEditingId(memory.id);
                                setEditContent(memory.content);
                                }}
                                className="text-gray-400 hover:text-blue-400"
                            >
                                <Edit2 size={14} />
                            </button>
                            <button 
                                onClick={() => handleDelete(memory.id)}
                                className="text-gray-400 hover:text-red-400"
                            >
                                <Trash2 size={14} />
                            </button>
                            </div>
                        </div>
                        <p className="text-gray-300 text-sm leading-relaxed">{memory.content}</p>
                        <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
                            <span>{new Date(memory.timestamp).toLocaleDateString()}</span>
                            {memory.tags && memory.tags.length > 0 && (
                                <div className="flex gap-1">
                                    {memory.tags.map(tag => (
                                        <span key={tag} className="bg-gray-700 px-1.5 rounded text-gray-400">#{tag}</span>
                                    ))}
                                </div>
                            )}
                        </div>
                        </>
                    )}
                    </div>
                ))}
                {memories.length === 0 && !isAdding && (
                    <div className="text-center text-gray-500 py-8 text-sm">
                    No memories found.
                    </div>
                )}
                </div>
            </>
        )}
      </div>

      {/* Action Detail Modal */}
      {selectedAction && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setSelectedAction(null)}>
            <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 max-w-md w-full shadow-2xl transform transition-all scale-100" onClick={e => e.stopPropagation()}>
                <div className="flex justify-between items-start mb-4">
                    <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${
                            selectedAction.category === 'coding' ? 'bg-purple-900/50 text-purple-400' :
                            selectedAction.category === 'social' ? 'bg-red-900/50 text-red-400' :
                            selectedAction.category === 'memory' ? 'bg-blue-900/50 text-blue-400' :
                            'bg-gray-700 text-gray-300'
                        }`}>
                            <Zap size={24} />
                        </div>
                        <div>
                            <h3 className="text-xl font-bold text-white">{selectedAction.name}</h3>
                            <span className="text-xs text-gray-400 uppercase tracking-wider">{selectedAction.category}</span>
                        </div>
                    </div>
                    <button onClick={() => setSelectedAction(null)} className="text-gray-400 hover:text-white transition-colors">
                        <X size={24} />
                    </button>
                </div>
                
                <div className="space-y-6">
                    <div>
                        <h4 className="text-sm font-semibold text-gray-300 mb-2">Description</h4>
                        <p className="text-gray-400 text-sm leading-relaxed bg-gray-900/50 p-3 rounded-lg border border-gray-700/50">
                            {selectedAction.description}
                        </p>
                    </div>
                    
                    {Object.keys(selectedAction.parameters).length > 0 ? (
                        <div>
                            <h4 className="text-sm font-semibold text-gray-300 mb-2">Parameters</h4>
                            <div className="bg-gray-900 rounded-lg border border-gray-700 overflow-hidden">
                                {Object.entries(selectedAction.parameters).map(([key, desc], index) => (
                                    <div key={key} className={`p-3 grid grid-cols-12 gap-4 text-sm ${index !== 0 ? 'border-t border-gray-800' : ''}`}>
                                        <span className="font-mono text-purple-400 col-span-4 font-medium">{key}</span>
                                        <span className="text-gray-400 col-span-8">{desc}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ) : (
                        <div className="text-sm text-gray-500 italic">No parameters required.</div>
                    )}
                </div>
            </div>
        </div>
      )}
    </div>
  );
};


