import { useWebSocket } from './hooks/useWebSocket';
import { ChatWindow } from './components/ChatWindow';
import { MemoryManager } from './components/MemoryManager';
import { AgentStateDashboard } from './components/AgentStateDashboard';
import { CharacterDisplay } from './components/CharacterDisplay';
import { ThinkingPool } from './components/ThinkingPool';
import { useMemo } from 'react';

function App() {
  // Persist User ID in localStorage
  const userId = useMemo(() => {
    let id = localStorage.getItem("alice_user_id");
    if (!id) {
      id = "user_" + Math.random().toString(36).substr(2, 9);
      localStorage.setItem("alice_user_id", id);
    }
    return id;
  }, []);

  const wsUrl = `ws://localhost:8000/ws/${userId}`;
  const { messages, sendMessage, isConnected, agentState, visualState, backgroundColor, actionQueue } = useWebSocket(wsUrl);

  const handleTerminateThinking = async (itemId: string) => {
    try {
      await fetch(`http://localhost:8000/agent/${userId}/thinking-pool/${itemId}`, {
        method: 'DELETE',
      });
      // The state update will come via WebSocket eventually, 
      // but we could also optimistically update if we had a setter for agentState.
      // For now, we rely on the backend to push the update or the next poll.
    } catch (error) {
      console.error("Failed to terminate thinking item", error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 p-4 md:p-6 flex flex-col md:flex-row gap-6">
      {/* Left Column: Character & State */}
      <div className="w-full md:w-80 h-[85vh] md:h-[90vh] flex flex-col gap-4">
        {/* Top Left: Character Display */}
        <div className="h-1/2 min-h-[16rem]">
            <CharacterDisplay visualState={visualState} backgroundColor={backgroundColor} />
        </div>
        {/* Bottom Left: Agent State */}
        <div className="h-1/2 min-h-0">
            <AgentStateDashboard state={agentState} userId={userId} />
        </div>
      </div>

      {/* Middle Column: Chat */}
      <div className="flex-1 h-[85vh] md:h-[90vh]">
        <ChatWindow 
          messages={messages} 
          onSendMessage={sendMessage} 
          isConnected={isConnected}
          userId={userId}
        />
      </div>

      {/* Right Column: Memory & Thinking Pool */}
      <div className="w-full md:w-80 h-[85vh] md:h-[90vh] flex flex-col gap-4">
        {/* Top Right: Memory */}
        <div className="h-1/2 min-h-0">
            <MemoryManager userId={userId} agentState={agentState} />
        </div>
        {/* Bottom Right: Thinking Pool */}
        <div className="h-1/2 min-h-0">
            <ThinkingPool 
              pool={agentState?.goals?.thinking_pool || []} 
              actionQueue={actionQueue}
              onTerminate={handleTerminateThinking}
            />
        </div>
      </div>
    </div>
  );
}

export default App;
