import React from 'react';

interface ThinkingPoolItem {
  id: string;
  topic: string;
  content: string;
  status: 'active' | 'pending' | 'completed';
}

interface ActionQueueItem {
  name: string;
  parameters: any;
  status: 'pending' | 'executing' | 'completed' | 'failed';
  result?: any;
}

interface ThinkingPoolProps {
  pool: ThinkingPoolItem[];
  actionQueue?: ActionQueueItem[];
  onTerminate?: (id: string) => void;
}

export const ThinkingPool: React.FC<ThinkingPoolProps> = ({ pool, actionQueue = [], onTerminate }) => {
  return (
    <div className="bg-gray-900 rounded-lg p-4 border border-gray-800 h-full overflow-y-auto flex flex-col gap-6">
      
      {/* Action Queue Section */}
      <div>
        <h2 className="text-lg font-semibold text-blue-400 mb-3 flex items-center gap-2">
          <span>⚡</span> Action Queue
        </h2>
        {(!actionQueue || actionQueue.length === 0) ? (
           <div className="text-gray-500 text-sm italic text-center py-4 border border-dashed border-gray-800 rounded">
             No pending actions.
           </div>
        ) : (
          <div className="space-y-2">
            {actionQueue.map((item, idx) => (
              <div 
                key={idx} 
                className={`p-3 rounded border flex flex-col gap-2 ${
                  item.status === 'executing' ? 'bg-blue-900/20 border-blue-500/50' : 
                  item.status === 'completed' ? 'bg-green-900/20 border-green-500/50 opacity-70' :
                  item.status === 'failed' ? 'bg-red-900/20 border-red-500/50' :
                  'bg-gray-800 border-gray-700'
                }`}
              >
                <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                        <span className="font-mono text-sm text-blue-300 font-bold">{item.name}</span>
                        {item.status === 'executing' && (
                        <span className="flex h-2 w-2 relative">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
                        </span>
                        )}
                    </div>
                    <span className={`text-[10px] px-2 py-1 rounded uppercase font-bold tracking-wider ${
                    item.status === 'executing' ? 'bg-blue-500 text-white' :
                    item.status === 'completed' ? 'bg-green-500 text-white' :
                    item.status === 'failed' ? 'bg-red-500 text-white' :
                    'bg-gray-700 text-gray-300'
                    }`}>
                    {item.status}
                    </span>
                </div>

                <div className="text-xs text-gray-400 truncate font-mono" title={JSON.stringify(item.parameters, null, 2)}>
                    {item.name === 'browse_web' && item.parameters?.query ? (
                        <span className="text-gray-300">Query: <span className="text-white">{item.parameters.query}</span></span>
                    ) : item.name === 'think_add' && item.parameters ? (
                        <div className="flex flex-col gap-1">
                            <span className="text-purple-300 font-bold">New Chain: <span className="text-white">{item.parameters.topic || 'Unknown'}</span></span>
                            <span className="text-gray-400 italic">"{item.parameters.content || ''}"</span>
                        </div>
                    ) : item.name === 'think_update' && item.parameters ? (
                        <div className="flex flex-col gap-1">
                            <span className="text-blue-300 font-bold">Update Chain #{item.parameters.chain_id || '?'}</span>
                            <span className="text-gray-400 italic">"{item.parameters.content || ''}"</span>
                        </div>
                    ) : item.name === 'think_complete' && item.parameters ? (
                        <div className="flex flex-col gap-1">
                            <span className="text-green-300 font-bold">Complete Chain #{item.parameters.chain_id || '?'}</span>
                            {item.parameters.content && <span className="text-gray-400 italic">"{item.parameters.content}"</span>}
                        </div>
                    ) : (
                        JSON.stringify(item.parameters || {})
                    )}
                </div>

                {/* Result display for completed items */}
                {item.status === 'completed' && item.result && (
                    <div className="text-[10px] text-green-400/90 border-t border-green-500/20 pt-2 mt-1">
                        {item.name === 'browse_web' && item.result.data?.title ? (
                            <div className="flex flex-col gap-1">
                                <span className="font-bold">Found:</span>
                                <a href={item.result.data.url} target="_blank" rel="noopener noreferrer" className="hover:underline truncate block text-blue-300">
                                    {item.result.data.title}
                                </a>
                                {item.result.data.extracted_links && item.result.data.extracted_links.length > 0 && (
                                  <div className="mt-1 pl-2 border-l border-gray-700">
                                    <span className="text-gray-500 text-[9px] uppercase font-bold">Related Links:</span>
                                    <div className="flex flex-col gap-0.5 mt-0.5">
                                      {item.result.data && Array.isArray(item.result.data.extracted_links) && item.result.data.extracted_links.slice(0, 5).map((link: any, i: number) => (
                                        <div key={i} className="flex gap-1 items-center">
                                          <span className="text-gray-600">-</span>
                                          <a href={link?.url || '#'} target="_blank" rel="noopener noreferrer" className="hover:underline truncate text-gray-400 hover:text-blue-300" title={link?.url}>
                                            {link?.text || link?.url || 'Link'}
                                          </a>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}
                            </div>
                        ) : (
                            <div className="truncate" title={item.result.message}>
                                {item.result.message || "Action completed successfully."}
                            </div>
                        )}
                    </div>
                )}
                
                {item.status === 'failed' && item.result && (
                     <div className="text-[10px] text-red-400/90 border-t border-red-500/20 pt-2 mt-1 truncate" title={item.result.error}>
                        Error: {item.result.error}
                     </div>
                )}

              </div>
            ))}
          </div>
        )}
      </div>

      {/* Thinking Pool Section */}
      <div>
        <h2 className="text-lg font-semibold text-purple-400 mb-3 flex items-center gap-2">
          <span>🧠</span> Thinking Pool
        </h2>
        {(!pool || pool.length === 0) ? (
          <div className="text-gray-500 text-sm italic text-center py-4 border border-dashed border-gray-800 rounded">
            No active thought threads.
          </div>
        ) : (
          <div className="space-y-3">
            {pool.map((item) => (
              <div 
                key={item.id} 
                className={`p-3 rounded border ${
                  item.status === 'active' ? 'bg-purple-900/20 border-purple-500/50' : 
                  item.status === 'completed' ? 'bg-green-900/20 border-green-500/50 opacity-70' :
                  'bg-gray-800 border-gray-700'
                }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-gray-400">
                      {item.topic}
                    </span>
                    {onTerminate && (
                      <button 
                        onClick={() => onTerminate(item.id)}
                        className="text-gray-500 hover:text-red-400 transition-colors p-0.5 rounded hover:bg-red-900/20"
                        title="Terminate this thought thread"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <line x1="18" y1="6" x2="6" y2="18"></line>
                          <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                      </button>
                    )}
                  </div>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded uppercase ${
                    item.status === 'active' ? 'bg-purple-500 text-white' :
                    item.status === 'completed' ? 'bg-green-500 text-white' :
                    'bg-gray-600 text-gray-300'
                  }`}>
                    {item.status}
                  </span>
                </div>
                
                <div className="space-y-1">
                  {Array.isArray(item.content) ? (
                    item.content.map((step, index, array) => (
                      <div key={index} className="flex gap-2 group">
                         <div className="flex flex-col items-center min-w-[10px]">
                            {/* Dot */}
                            <div className={`w-2 h-2 rounded-full mt-2 ${
                              index === array.length - 1 && item.status === 'active' 
                                ? 'bg-purple-400 animate-pulse shadow-[0_0_8px_rgba(192,132,252,0.6)]' 
                                : 'bg-gray-600'
                            }`}></div>
                            {/* Line connecting to next */}
                            {index < array.length - 1 && (
                              <div className="w-0.5 flex-1 bg-gray-700/50 my-0.5"></div>
                            )}
                         </div>
                         <div className="flex-1 bg-black/20 hover:bg-black/40 transition-colors p-2 rounded text-xs text-gray-300 border border-white/5 leading-relaxed">
                           {typeof step === 'string' ? step.trim() : JSON.stringify(step)}
                         </div>
                      </div>
                    ))
                  ) : (
                    // Fallback for old string format
                    (item.content || "").split('->').map((step, index, array) => (
                      <div key={index} className="flex gap-2 group">
                         <div className="flex flex-col items-center min-w-[10px]">
                            {/* Dot */}
                            <div className={`w-2 h-2 rounded-full mt-2 ${
                              index === array.length - 1 && item.status === 'active' 
                                ? 'bg-purple-400 animate-pulse shadow-[0_0_8px_rgba(192,132,252,0.6)]' 
                                : 'bg-gray-600'
                            }`}></div>
                            {/* Line connecting to next */}
                            {index < array.length - 1 && (
                              <div className="w-0.5 flex-1 bg-gray-700/50 my-0.5"></div>
                            )}
                         </div>
                         <div className="flex-1 bg-black/20 hover:bg-black/40 transition-colors p-2 rounded text-xs text-gray-300 border border-white/5 leading-relaxed">
                           {step.trim()}
                         </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
