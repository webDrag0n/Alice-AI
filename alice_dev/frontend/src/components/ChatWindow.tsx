import React, { useState, useRef, useEffect } from 'react';
import { Message } from '../hooks/useWebSocket';
import { Send, User, BrainCircuit, Zap, Database, Lightbulb, Save, BookOpen, Heart, Star, Smile, Archive, Terminal, Code, Clock, Globe, Search, FileText, Folder, Download, Edit, PlusSquare } from 'lucide-react';

interface ChatWindowProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
  isConnected: boolean;
  userId?: string;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({ messages, onSendMessage, isConnected, userId }) => {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && isConnected) {
      onSendMessage(input);
      setInput('');
    }
  };

  return (
    <div className="flex flex-col h-full max-w-3xl mx-auto bg-gray-800 rounded-lg shadow-xl overflow-hidden border border-gray-700">
      {/* Header */}
      <div className="bg-gray-900 p-4 border-b border-gray-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <h2 className="text-xl font-semibold text-gray-100">Alice</h2>
        </div>
        <div className="flex flex-col items-end">
            <span className="text-xs text-gray-500">v0.1.0 PoC</span>
            {userId && <span className="text-xs text-gray-600 font-mono">ID: {userId}</span>}
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-10">
            <p>Say hello to Alice.</p>
          </div>
        )}
        
        {messages.map((msg, idx) => {

            if (msg.role === 'thinking_process') {
                return (
                    <div key={idx} className="flex justify-start px-12 opacity-90 my-2">
                        <div className="bg-[#1a1b26] border-l-2 border-purple-500 text-gray-300 p-3 rounded-r-lg text-xs font-mono w-full max-w-[90%] shadow-lg">
                            <div className="flex items-center gap-2 mb-2 text-purple-400 border-b border-gray-800 pb-1">
                                <BrainCircuit size={14} />
                                <span className="uppercase tracking-wider text-[10px] font-bold">Thinking Chain Update</span>
                            </div>
                            <div className="space-y-1">
                                {(msg.content || '').split('\n').map((line, i) => {
                                    if (line.startsWith('▶')) return <p key={i} className="text-green-400 font-semibold">{line}</p>;
                                    if (line.startsWith('▷')) return <p key={i} className="text-blue-300">{line}</p>;
                                    if (line.startsWith('■')) return <p key={i} className="text-gray-500 line-through">{line}</p>;
                                    return <p key={i} className="pl-4 text-gray-400">{line}</p>;
                                })}
                            </div>
                        </div>
                    </div>
                );
            }

            if (msg.role === 'action') {
                const { actionData } = msg;
                const eventType = actionData?.event;

                // Handle Thinking Chain Operations with special style
                if (eventType === 'think_add' || eventType === 'think_update' || eventType === 'think_complete') {
                    let lineContent = '';
                    const data = actionData.data || {};
                    
                    if (eventType === 'think_add') {
                        lineContent = `▶ New Chain: [${data.topic || 'Unknown'}] ${data.content || ''}`;
                    } else if (eventType === 'think_update') {
                        lineContent = `▷ Update Chain #${data.chain_id || '?'}: ${data.content || ''}`;
                    } else if (eventType === 'think_complete') {
                        lineContent = `■ Complete Chain #${data.chain_id || '?'}: ${data.content || ''}`;
                    }

                    return (
                        <div key={idx} className="flex justify-start px-12 opacity-90 my-2">
                            <div className="bg-[#1a1b26] border-l-2 border-purple-500 text-gray-300 p-3 rounded-r-lg text-xs font-mono w-full max-w-[90%] shadow-lg">
                                <div className="flex items-center gap-2 mb-2 text-purple-400 border-b border-gray-800 pb-1">
                                    <BrainCircuit size={14} />
                                    <span className="uppercase tracking-wider text-[10px] font-bold">Thinking Chain Update</span>
                                </div>
                                <div className="space-y-1">
                                    {lineContent.startsWith('▶') && <p className="text-green-400 font-semibold">{lineContent}</p>}
                                    {lineContent.startsWith('▷') && <p className="text-blue-300">{lineContent}</p>}
                                    {lineContent.startsWith('■') && <p className="text-gray-500 line-through">{lineContent}</p>}
                                </div>
                            </div>
                        </div>
                    );
                }

                // Handle Run Bash with Terminal Style
                if (eventType === 'run_bash') {
                    const { command, output, error, return_code } = actionData.data || {};
                    return (
                        <div key={idx} className="flex flex-col gap-2 my-4 px-8 opacity-95">
                            <div className="bg-[#0d1117] rounded-md overflow-hidden border border-gray-700 font-mono text-xs shadow-xl max-w-full">
                                <div className="bg-[#161b22] px-3 py-2 flex items-center gap-2 border-b border-gray-700">
                                    <div className="flex gap-1.5">
                                        <div className="w-2.5 h-2.5 rounded-full bg-red-500/80"></div>
                                        <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/80"></div>
                                        <div className="w-2.5 h-2.5 rounded-full bg-green-500/80"></div>
                                    </div>
                                    <div className="flex-1 text-center mr-12">
                                        <span className="text-gray-400 text-[10px]">bash — 80x24</span>
                                    </div>
                                </div>
                                <div className="p-3 text-gray-300 overflow-x-auto">
                                    <div className="flex gap-2 text-blue-400 mb-1">
                                        <span>➜</span>
                                        <span className="text-cyan-300">~</span>
                                        <span className="text-gray-100">{command}</span>
                                    </div>
                                    {output && <div className="whitespace-pre-wrap text-gray-300 leading-relaxed">{output}</div>}
                                    {error && <div className="whitespace-pre-wrap text-red-400 mt-2">{error}</div>}
                                    {!output && !error && <div className="text-gray-600 italic mt-1">No output</div>}
                                </div>
                                <div className="bg-[#161b22] px-3 py-1 text-[10px] text-gray-500 flex justify-between items-center border-t border-gray-800">
                                    <span>alice@dev</span>
                                    <span className={return_code === 0 ? "text-green-500" : "text-red-500"}>
                                        Exit Code: {return_code}
                                    </span>
                                </div>
                            </div>
                        </div>
                    );
                }

                // Default style
                let icon = <Zap size={12} className="text-yellow-400" />;
                let content = <span className="font-medium">{msg.content}</span>;
                let details = null;

                if (eventType === 'recall' || eventType === 'associate') {
                    return (
                        <div key={idx} className="flex flex-col items-center my-4 w-full px-8">
                            <div className="w-full max-w-2xl bg-[#1a1b26] rounded-lg border border-blue-500/30 shadow-lg overflow-hidden">
                                {/* Header */}
                                <div className="bg-blue-900/20 px-3 py-2 flex items-center justify-between border-b border-blue-500/20">
                                    <div className="flex items-center gap-2 text-blue-300">
                                        {eventType === 'recall' ? <Database size={14} /> : <Lightbulb size={14} />}
                                        <span className="text-xs font-bold uppercase tracking-wider">
                                            {eventType === 'recall' ? 'Memory Retrieval' : 'Cognitive Association'}
                                        </span>
                                    </div>
                                    <div className="text-[10px] text-blue-400/60 font-mono">
                                        {actionData.data?.length || 0} results found
                                    </div>
                                </div>
                                
                                {/* Content */}
                                <div className="p-3 space-y-2">
                                    <div className="text-xs text-gray-400 italic mb-2 flex items-center gap-2">
                                        <span className="w-1 h-1 rounded-full bg-blue-400"></span>
                                        {msg.content}
                                    </div>
                                    {actionData.data && Array.isArray(actionData.data) && actionData.data.map((item: any, i: number) => (
                                        <div key={i} className="bg-black/20 rounded p-2 border border-white/5 hover:border-blue-500/30 transition-colors group">
                                            <div className="flex items-start gap-2">
                                                <div className="mt-0.5 text-blue-500/50 group-hover:text-blue-400 transition-colors">
                                                    <BrainCircuit size={12} />
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-xs text-gray-300 leading-relaxed break-words">{item ? (item.content || JSON.stringify(item)) : ''}</p>
                                                    {item && item.timestamp && (
                                                        <div className="mt-1 flex items-center gap-2 text-[9px] text-gray-600">
                                                            <Clock size={8} />
                                                            <span>{new Date(item.timestamp).toLocaleString()}</span>
                                                            {item.importance && (
                                                                <span className="bg-blue-900/30 text-blue-300 px-1 rounded">
                                                                    IMP: {Number(item.importance).toFixed(2)}
                                                                </span>
                                                            )}
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    );
                } else if (eventType === 'memorize') {
                    return (
                        <div key={idx} className="flex flex-col items-center my-4 w-full px-8">
                            <div className="w-full max-w-2xl bg-[#1a1b26] rounded-lg border border-green-500/30 shadow-lg overflow-hidden">
                                {/* Header */}
                                <div className="bg-green-900/20 px-3 py-2 flex items-center justify-between border-b border-green-500/20">
                                    <div className="flex items-center gap-2 text-green-300">
                                        <Save size={14} />
                                        <span className="text-xs font-bold uppercase tracking-wider">
                                            Memory Consolidation
                                        </span>
                                    </div>
                                    <div className="text-[10px] text-green-400/60 font-mono">
                                        Long-term Storage
                                    </div>
                                </div>
                                
                                {/* Content */}
                                <div className="p-4 relative overflow-hidden">
                                    {/* Background decoration */}
                                    <div className="absolute top-0 right-0 -mt-4 -mr-4 text-green-500/5 pointer-events-none">
                                        <BrainCircuit size={100} />
                                    </div>
                                    
                                    <div className="relative z-10">
                                        <div className="text-xs text-gray-400 mb-2 flex items-center gap-2">
                                            <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
                                            Writing to episodic memory...
                                        </div>
                                        <div className="bg-black/30 rounded-lg p-3 border border-green-500/20 text-green-100/90 text-sm font-serif italic leading-relaxed shadow-inner">
                                            "{actionData.data}"
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    );
                } else if (eventType === 'check_time') {
                    icon = <Clock size={12} className="text-purple-400" />;
                    if (actionData.data) {
                        details = (
                           <div className="mt-2 text-[10px] text-gray-400 bg-black/20 p-2 rounded border border-white/5 w-full font-mono">
                               {actionData.data}
                           </div>
                       );
                   }
                } else if (eventType === 'learn_skill') {
                    icon = <BookOpen size={12} className="text-purple-400" />;
                } else if (eventType === 'relationship_update') {
                    icon = <Heart size={12} className="text-pink-500" />;
                    if (actionData.data) {
                        details = (
                            <div className="mt-2 text-[10px] text-gray-400 bg-black/20 p-2 rounded border border-white/5 w-full">
                                <div className="grid grid-cols-2 gap-2">
                                    <span>Intimacy: {actionData.data.intimacy}</span>
                                    <span>Trust: {actionData.data.trust}</span>
                                    <span className="col-span-2">Stage: {actionData.data.stage}</span>
                                </div>
                            </div>
                        );
                    }
                } else if (eventType === 'new_belief') {
                    icon = <Star size={12} className="text-orange-400" />;
                    if (actionData.data) {
                         details = (
                            <div className="mt-2 text-[10px] text-gray-400 bg-black/20 p-2 rounded border border-white/5 w-full italic">
                                "{actionData.data}"
                            </div>
                        );
                    }
                } else if (eventType === 'express') {
                    icon = <Smile size={12} className="text-cyan-400" />;
                } else if (eventType === 'auto_save') {
                    icon = <Archive size={12} className="text-gray-500" />;
                    // Auto-save is usually frequent, so we might keep it minimal
                    // or just show the icon and "Archiving..."
                } else if (eventType === 'run_code') {
                    // Special full-width terminal style for code execution
                    return (
                        <div key={idx} className="flex flex-col items-center my-4 w-full px-8">
                            <div className="w-full max-w-2xl bg-[#1e1e1e] rounded-lg border border-gray-700 shadow-2xl overflow-hidden font-mono text-xs">
                                {/* Terminal Header */}
                                <div className="bg-[#2d2d2d] px-3 py-1.5 flex items-center justify-between border-b border-black/50">
                                    <div className="flex items-center gap-1.5">
                                        <div className="w-2.5 h-2.5 rounded-full bg-[#ff5f56]"></div>
                                        <div className="w-2.5 h-2.5 rounded-full bg-[#ffbd2e]"></div>
                                        <div className="w-2.5 h-2.5 rounded-full bg-[#27c93f]"></div>
                                    </div>
                                    <div className="flex items-center gap-2 text-gray-400">
                                        <Terminal size={10} />
                                        <span className="text-[10px]">alice@soul-os:~/sandbox</span>
                                    </div>
                                    <div className="w-8"></div> {/* Spacer for centering */}
                                </div>
                                
                                {/* Terminal Content */}
                                <div className="p-3 space-y-2">
                                    {/* Input Command */}
                                    <div className="flex gap-2 text-green-400">
                                        <span className="select-none">➜</span>
                                        <span className="select-none">~</span>
                                        <span className="text-gray-300">python3 execute_script.py</span>
                                    </div>
                                    
                                    {/* Code Block */}
                                    <div className="bg-black/30 rounded p-2 border border-white/5 relative group">
                                        <div className="absolute top-1 right-2 text-[9px] text-gray-600 uppercase tracking-wider select-none">Python Script</div>
                                        <pre className="text-blue-300 overflow-x-auto whitespace-pre-wrap">{actionData.data.code}</pre>
                                    </div>

                                    {/* Output */}
                                    <div className="pt-1">
                                        <div className="text-gray-500 text-[10px] mb-1 select-none">Console Output:</div>
                                        <pre className="text-gray-300 whitespace-pre-wrap pl-2 border-l-2 border-gray-700">
                                            {actionData.data.output || <span className="text-gray-600 italic">(No output)</span>}
                                        </pre>
                                    </div>

                                    {/* Images */}
                                    {actionData.data.images && actionData.data.images.length > 0 && (
                                        <div className="pt-2 space-y-2">
                                            <div className="text-gray-500 text-[10px] mb-1 select-none">Generated Plots:</div>
                                            {actionData.data.images.map((img: string, i: number) => (
                                                <div key={i} className="bg-white rounded p-1">
                                                    <img src={`data:image/png;base64,${img}`} alt={`Plot ${i+1}`} className="w-full rounded" />
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                    
                                    {/* Cursor */}
                                    <div className="flex gap-2 text-green-400 animate-pulse">
                                        <span className="select-none">➜</span>
                                        <span className="select-none">~</span>
                                        <span className="w-1.5 h-3 bg-gray-500 block mt-1"></span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    );
                } else if (eventType === 'run_code_error') {
                    return (
                        <div key={idx} className="flex flex-col items-center my-4 w-full px-8">
                            <div className="w-full max-w-2xl bg-[#1e1e1e] rounded-lg border border-red-900/50 shadow-2xl overflow-hidden font-mono text-xs">
                                {/* Terminal Header (Error) */}
                                <div className="bg-[#2d1a1a] px-3 py-1.5 flex items-center justify-between border-b border-red-900/30">
                                    <div className="flex items-center gap-1.5">
                                        <div className="w-2.5 h-2.5 rounded-full bg-[#ff5f56]"></div>
                                        <div className="w-2.5 h-2.5 rounded-full bg-[#ffbd2e]"></div>
                                        <div className="w-2.5 h-2.5 rounded-full bg-[#27c93f]"></div>
                                    </div>
                                    <div className="flex items-center gap-2 text-red-400">
                                        <Terminal size={10} />
                                        <span className="text-[10px]">alice@soul-os:~/sandbox (ERROR)</span>
                                    </div>
                                    <div className="w-8"></div>
                                </div>
                                
                                <div className="p-3 space-y-2">
                                    <div className="bg-black/30 rounded p-2 border border-red-500/10">
                                        <pre className="text-blue-300/50 overflow-x-auto whitespace-pre-wrap">{actionData.data.code}</pre>
                                    </div>
                                    <div className="pt-1">
                                        <div className="text-red-500 font-bold mb-1">Runtime Error:</div>
                                        <pre className="text-red-300 whitespace-pre-wrap pl-2 border-l-2 border-red-700">
                                            {actionData.data.error}
                                        </pre>
                                    </div>
                                </div>
                            </div>
                        </div>
                    );
                } else if (eventType === 'skill_updated') {
                    icon = <Code size={12} className="text-purple-400" />;
                    if (actionData.data) {
                        details = (
                            <div className="mt-2 text-[10px] font-mono bg-purple-900/20 p-2 rounded border border-purple-500/20 w-full">
                                <div className="text-purple-300 font-bold mb-1">New Skill Code:</div>
                                <pre className="text-purple-200 overflow-x-auto max-h-32">{actionData.data}</pre>
                            </div>
                        );
                    }
                } else if (eventType === 'visit_page') {
                    icon = <Globe size={12} className="text-cyan-400" />;
                    content = <span className="font-medium">Visiting Link</span>;
                    details = (
                        <div className="mt-2 w-full bg-gray-900/50 rounded-lg border border-gray-700 overflow-hidden">
                            <div className="bg-gray-800 px-3 py-2 flex items-center justify-between border-b border-gray-700">
                                <div className="flex items-center gap-2 overflow-hidden">
                                    <Globe size={14} className="text-cyan-400 flex-shrink-0" />
                                    <span className="text-xs font-medium text-gray-200 truncate" title={actionData.data.title}>{actionData.data.title}</span>
                                </div>
                                <div className="text-[10px] text-gray-500 font-mono flex-shrink-0 ml-2">
                                    {new URL(actionData.data.url).hostname}
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-px bg-gray-700 border-b border-gray-700">
                                <div className="bg-gray-900/50 p-2 text-center">
                                    <div className="text-[10px] text-gray-500 uppercase tracking-wider">Words</div>
                                    <div className="text-xs font-mono text-gray-300">{actionData.data.stats.word_count}</div>
                                </div>
                                <div className="bg-gray-900/50 p-2 text-center">
                                    <div className="text-[10px] text-gray-500 uppercase tracking-wider">Links</div>
                                    <div className="text-xs font-mono text-gray-300">{actionData.data.stats.link_count}</div>
                                </div>
                            </div>
                        </div>
                    );
                } else if (eventType === 'download_file') {
                    icon = <Download size={12} className="text-green-400" />;
                    content = <span className="font-medium">Downloaded File</span>;
                    details = (
                        <div className="mt-2 w-full bg-gray-900/50 rounded-lg border border-gray-700 p-3">
                            <div className="flex items-center gap-3">
                                <div className="bg-green-900/30 p-2 rounded text-green-400">
                                    <FileText size={20} />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="text-xs font-medium text-gray-200 truncate">{actionData.data.path.split('/').pop()}</div>
                                    <div className="text-[10px] text-gray-500 truncate">{actionData.data.url}</div>
                                </div>
                                <div className="text-xs font-mono text-gray-400">
                                    {Math.round(actionData.data.size / 1024)} KB
                                </div>
                            </div>
                        </div>
                    );
                } else if (eventType === 'list_files') {
                    icon = <Folder size={12} className="text-yellow-400" />;
                    content = <span className="font-medium">List Files</span>;
                    details = (
                        <div className="mt-2 w-full bg-gray-900/50 rounded-lg border border-gray-700 overflow-hidden">
                            <div className="bg-gray-800 px-3 py-2 text-xs font-mono text-gray-400 border-b border-gray-700">
                                {actionData.data.path}
                            </div>
                            <div className="p-2 grid grid-cols-2 gap-2">
                                {actionData.data.files.map((f: string, i: number) => (
                                    <div key={i} className="flex items-center gap-2 text-xs text-gray-300 bg-black/20 px-2 py-1 rounded">
                                        {f.endsWith('/') ? <Folder size={10} className="text-yellow-500" /> : <FileText size={10} className="text-gray-500" />}
                                        <span className="truncate">{f}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    );
                } else if (eventType === 'read_file') {
                    icon = <FileText size={12} className="text-blue-400" />;
                    content = <span className="font-medium">Read File</span>;
                    details = (
                        <div className="mt-2 w-full bg-gray-900/50 rounded-lg border border-gray-700 overflow-hidden">
                            <div className="bg-gray-800 px-3 py-2 flex justify-between items-center border-b border-gray-700">
                                <span className="text-xs font-mono text-gray-400">{actionData.data.path}</span>
                                <span className="text-[10px] text-gray-500">{actionData.data.total_lines} lines</span>
                            </div>
                            <pre className="p-3 text-xs text-gray-300 font-mono overflow-x-auto whitespace-pre-wrap max-h-60">
                                {actionData.data.content}
                            </pre>
                            {actionData.data.truncated && (
                                <div className="bg-gray-800/50 px-3 py-1 text-[10px] text-gray-500 text-center italic">
                                    Content truncated...
                                </div>
                            )}
                        </div>
                    );
                } else if (eventType === 'create_file') {
                    icon = <PlusSquare size={12} className="text-green-400" />;
                    content = <span className="font-medium">Created File</span>;
                    details = (
                        <div className="mt-2 w-full bg-gray-900/50 rounded-lg border border-gray-700 p-3 flex items-center gap-3">
                            <div className="bg-green-900/30 p-2 rounded text-green-400">
                                <FileText size={20} />
                            </div>
                            <div>
                                <div className="text-xs font-medium text-gray-200">{actionData.data.path}</div>
                                <div className="text-[10px] text-gray-500">{actionData.data.size} bytes written</div>
                            </div>
                        </div>
                    );
                } else if (eventType === 'edit_file') {
                    icon = <Edit size={12} className="text-orange-400" />;
                    content = <span className="font-medium">Edited File</span>;
                    details = (
                        <div className="mt-2 w-full bg-gray-900/50 rounded-lg border border-gray-700 p-3 flex items-center gap-3">
                            <div className="bg-orange-900/30 p-2 rounded text-orange-400">
                                <Edit size={20} />
                            </div>
                            <div>
                                <div className="text-xs font-medium text-gray-200">{actionData.data.path}</div>
                                <div className="text-[10px] text-green-500">Successfully updated</div>
                            </div>
                        </div>
                    );
                } else if (eventType === 'web_browse') {
                    icon = actionData.data.is_search ? <Search size={12} className="text-blue-400" /> : <Globe size={12} className="text-cyan-400" />;
                    content = <span className="font-medium">{actionData.data.is_search ? "Searching Web" : "Browsing Web"}</span>;
                    
                    details = (
                        <div className="mt-2 w-full bg-gray-900/50 rounded-lg border border-gray-700 overflow-hidden">
                            {/* Header */}
                            <div className="bg-gray-800 px-3 py-2 flex items-center justify-between border-b border-gray-700">
                                <div className="flex items-center gap-2 overflow-hidden">
                                    {actionData.data.is_search ? <Search size={14} className="text-blue-400 flex-shrink-0" /> : <Globe size={14} className="text-cyan-400 flex-shrink-0" />}
                                    <span className="text-xs font-medium text-gray-200 truncate" title={actionData.data.title}>{actionData.data.title}</span>
                                </div>
                                <div className="text-[10px] text-gray-500 font-mono flex-shrink-0 ml-2">
                                    {new URL(actionData.data.url).hostname}
                                </div>
                            </div>
                            
                            {/* Stats Grid */}
                            <div className="grid grid-cols-3 gap-px bg-gray-700 border-b border-gray-700">
                                <div className="bg-gray-900/50 p-2 text-center">
                                    <div className="text-[10px] text-gray-500 uppercase tracking-wider">Words</div>
                                    <div className="text-xs font-mono text-gray-300">{actionData.data.stats.word_count}</div>
                                </div>
                                <div className="bg-gray-900/50 p-2 text-center">
                                    <div className="text-[10px] text-gray-500 uppercase tracking-wider">Links</div>
                                    <div className="text-xs font-mono text-gray-300">{actionData.data.stats.link_count}</div>
                                </div>
                                <div className="bg-gray-900/50 p-2 text-center">
                                    <div className="text-[10px] text-gray-500 uppercase tracking-wider">Size</div>
                                    <div className="text-xs font-mono text-gray-300">{Math.round(actionData.data.stats.content_length / 1024)}KB</div>
                                </div>
                            </div>

                            {/* Extracted Links (if any) */}
                            {actionData.data.extracted_links && actionData.data.extracted_links.length > 0 && (
                                <div className="p-2 bg-gray-900/30">
                                    <div className="text-[10px] text-gray-500 mb-1 px-1">Top Links Found:</div>
                                    <div className="space-y-1">
                                        {actionData.data.extracted_links.slice(0, 3).map((link: any, i: number) => (
                                            <div key={i} className="flex items-center gap-2 text-[10px] text-blue-400 bg-black/20 px-2 py-1 rounded hover:bg-black/40 transition-colors truncate">
                                                <span className="w-1 h-1 rounded-full bg-blue-500 flex-shrink-0"></span>
                                                <span className="truncate">{link.text || link.url}</span>
                                            </div>
                                        ))}
                                        {actionData.data.extracted_links.length > 3 && (
                                            <div className="text-[9px] text-gray-600 px-2 italic">
                                                + {actionData.data.extracted_links.length - 3} more links...
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    );
                }

                return (
                    <div key={idx} className="flex flex-col items-center my-2 w-full">
                        <div className="bg-gray-800/80 border border-blue-900/30 text-blue-300 px-4 py-1 rounded-full text-xs flex items-center gap-2 shadow-sm max-w-[90%]">
                            {icon}
                            {content}
                        </div>
                        {details && <div className="max-w-[80%] mt-1">{details}</div>}
                    </div>
                );
            }

            return (
              <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`flex max-w-[80%] ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'} gap-3`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === 'user' ? 'bg-blue-600' : 'bg-transparent-600 overflow-hidden'}`}>
                    {msg.role === 'user' ? <User size={16} /> : <img src="/character_images/avatar.png" alt="Alice" className="w-full h-full object-cover" />}
                  </div>
                  
                  <div className={`p-3 rounded-lg ${
                    msg.role === 'user' 
                      ? 'bg-blue-600 text-white rounded-tr-none' 
                      : 'bg-gray-700 text-gray-100 rounded-tl-none'
                  }`}>
                    <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</p>
                  </div>
                </div>
              </div>
            );
        })}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <form onSubmit={handleSubmit} className="p-4 bg-gray-900 border-t border-gray-700">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={isConnected ? "Type a message..." : "Connecting..."}
            disabled={!isConnected}
            className="flex-1 bg-gray-800 text-white border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!input.trim() || !isConnected}
            className="bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send size={20} />
          </button>
        </div>
      </form>
    </div>
  );
};
