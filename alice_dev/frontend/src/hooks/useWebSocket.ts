import { useState, useEffect, useRef, useCallback } from 'react';

export type Message = {
  role: 'user' | 'assistant' | 'thought' | 'action' | 'thinking_process';
  content: string;
  actionData?: any;
};

export type AgentState = {
  emotions: Record<string, number>;
  desires: Record<string, number>;
  goals: {
    life_goal?: string;
    long_term_goal?: string;
    short_term_goal?: string;
    thinking_pool?: any[];
  };
  instant_memory?: string[];
};

export type VisualState = {
  body: string;
  face: string;
};

export const useWebSocket = (url: string) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [agentState, setAgentState] = useState<AgentState | null>(null);
  const [visualState, setVisualState] = useState<VisualState>({ body: 'idle', face: 'neutral' });
  const [backgroundColor, setBackgroundColor] = useState<string>('bg-gray-900');
  const [actionQueue, setActionQueue] = useState<any[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const ws = useRef<WebSocket | null>(null);
  const currentResponseRef = useRef<string>("");

  useEffect(() => {
    ws.current = new WebSocket(url);

    ws.current.onopen = () => {
      console.log('Connected to WebSocket');
      setIsConnected(true);
    };

    ws.current.onclose = () => {
      console.log('Disconnected from WebSocket');
      setIsConnected(false);
    };

    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (!data) return;
        
        if (data.type === 'action_queue_update') {
            setActionQueue(Array.isArray(data.data) ? data.data : []);
        } else if (data.type === 'history_update') {
            // Map history items to Message format
            const history = Array.isArray(data.history) ? data.history : [];
            setMessages(history.map((msg: any) => {
                if (!msg) return { role: 'user', content: '' }; // Safe fallback
                let role = msg.role || msg.type || 'user';
                // Fix for legacy history where speak actions were stored as 'action' role
                if (role === 'action' && msg.actionData?.event === 'speak') {
                    role = 'assistant';
                }
                return {
                    role: role,
                    content: msg.content || '',
                    actionData: msg.actionData
                };
            }));
        } else if (data.type === 'agent_state') {
            setAgentState((prev) => {
                if (!prev) return data.data;
                return { ...prev, ...data.data };
            });
        } else if (data.type === 'agent_response_start') {
          currentResponseRef.current = "";
          setMessages((prev) => [...prev, { role: 'assistant', content: '' }]);
        } else if (data.type === 'agent_stream') {
          currentResponseRef.current += data.chunk;
          
          setMessages((prev) => {
            const newMessages = [...prev];
            // Find the last assistant message to update
            for (let i = newMessages.length - 1; i >= 0; i--) {
                if (newMessages[i].role === 'assistant') {
                    newMessages[i].content = currentResponseRef.current;
                    return newMessages;
                }
            }
            return [...newMessages, { role: 'assistant', content: currentResponseRef.current }];
          });
        } else if (data.type === 'agent_action') {
            const actionData = data.data;
            if (!actionData) return;
            
            // Determine role based on event type
            let role: Message['role'] = 'action';
            if (actionData.event === 'speak') {
                role = 'assistant';
            }

            setMessages((prev) => [...prev, { 
                role: role, 
                content: actionData.message,
                actionData: actionData
            }]);
            
            // Update Visual State if present
            if (actionData.visual_state) {
                setVisualState(actionData.visual_state);
            }

            // Handle Adjust Light
            if (actionData.event === 'adjust_light') {
                console.log("Adjusting light to:", actionData.data);
                const colorMap: Record<string, string> = {
                    'blue': 'bg-blue-900/50',
                    'warm': 'bg-orange-900/50',
                    'pink': 'bg-pink-900/50',
                    'red': 'bg-red-900/50',
                    'green': 'bg-green-900/50',
                    'purple': 'bg-purple-900/50',
                    'cyan': 'bg-cyan-900/50',
                    'yellow': 'bg-yellow-900/50',
                    'white': 'bg-gray-200',
                    'off': 'bg-black',
                    'default': 'bg-gray-900'
                };
                const colorKey = (actionData.data || 'default').toLowerCase();
                setBackgroundColor(colorMap[colorKey] || 'bg-gray-900');
            }
        } else if (data.type === 'agent_log') {
            // Handle logs (thoughts and state updates)
            const log = data.log;
            if (log && log.type === 'thought' && log.content) {
                const content = log.content;
                
                // Update Agent State
                setAgentState((prev) => {
                    const currentEmotions = prev?.emotions || {};
                    const currentDesires = prev?.desires || {};
                    const currentGoals = prev?.goals || {};
                    
                    return {
                        emotions: content.emotions_update || currentEmotions,
                        desires: content.desires_update || currentDesires,
                        goals: {
                            life_goal: content.life_goal || currentGoals.life_goal,
                            long_term_goal: content.long_term_goal || currentGoals.long_term_goal,
                            short_term_goal: content.short_term_goal || currentGoals.short_term_goal,
                            thinking_pool: Array.isArray(content.thinking_pool) ? content.thinking_pool : (currentGoals.thinking_pool || [])
                        },
                        instant_memory: Array.isArray(prev?.instant_memory) ? prev.instant_memory : []
                    };
                });

                // Add thought to chat if it exists
                if (content.thought) {
                    setMessages((prev) => [...prev, { role: 'thought', content: content.thought }]);
                }

                // Handle Thinking Process
                const actions = content.thinking_pool_actions;
                if (actions) {
                    let processText = "";
                    if (Array.isArray(actions.add)) {
                        actions.add.forEach((a: any) => {
                            processText += `▶ Started: ${a.topic}\n${a.content}\n`;
                        });
                    }
                    if (Array.isArray(actions.continue)) {
                        actions.continue.forEach((a: any) => {
                            processText += `▷ Continued [${a.id}]: ${a.new_content}\n`;
                        });
                    }
                    if (Array.isArray(actions.complete)) {
                        actions.complete.forEach((id: string) => {
                            processText += `■ Completed [${id}]\n`;
                        });
                    }
                    
                    if (processText) {
                        setMessages((prev) => [...prev, { 
                            role: 'thinking_process', 
                            content: processText.trim(),
                            actionData: actions
                        }]);
                    }
                }
            }
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [url]);

  const sendMessage = useCallback((content: string) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: 'chat_message', content }));
      setMessages((prev) => [...prev, { role: 'user', content }]);
    }
  }, []);

  return { messages, sendMessage, isConnected, agentState, visualState, backgroundColor, actionQueue };
};
