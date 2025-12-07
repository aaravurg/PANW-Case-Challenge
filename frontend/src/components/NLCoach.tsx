"use client";

import React, { useState, useRef, useEffect } from 'react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  functionCalls?: Array<{
    function: string;
    arguments: Record<string, any>;
    result: any;
  }>;
}

interface NLCoachProps {
  onClose?: () => void;
}

const NLCoach: React.FC<NLCoachProps> = ({ onClose }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: "Hi! I'm your financial coach. Ask me anything about your spending, subscriptions, or savings goals. For example:\n\n• How much did I spend on coffee last month?\n• What are my top spending categories?\n• Show me my subscriptions\n• Am I spending more this month than last?"
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationHistory, setConversationHistory] = useState<Array<any>>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');

    // Add user message to UI
    const newMessages = [...messages, { role: 'user' as const, content: userMessage }];
    setMessages(newMessages);
    setIsLoading(true);

    try {
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

      const response = await fetch(`${API_BASE_URL}/api/coach/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          conversation_history: conversationHistory,
          user_id: 'default_user'
        })
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to get response' }));
        throw new Error(error.detail || 'Failed to get response');
      }

      const data = await response.json();

      // Add assistant response to UI
      setMessages(prev => [...prev, {
        role: 'assistant' as const,
        content: data.response,
        functionCalls: data.function_calls
      }]);

      // Update conversation history for context
      setConversationHistory(data.conversation_history);

    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, {
        role: 'assistant' as const,
        content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}. Please try again.`
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
        <div>
          <h2 className="text-xl font-semibold text-gray-800">Financial Coach</h2>
          <p className="text-sm text-gray-500">Ask me anything about your finances</p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            aria-label="Close chat"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-3 ${
                message.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              <p className="whitespace-pre-wrap break-words">{message.content}</p>

              {/* Show function calls if present (for debugging/transparency) */}
              {message.functionCalls && message.functionCalls.length > 0 && (
                <details className="mt-2 text-xs opacity-75">
                  <summary className="cursor-pointer">Data queries ({message.functionCalls.length})</summary>
                  <div className="mt-1 space-y-1">
                    {message.functionCalls.map((call, i) => (
                      <div key={i} className="font-mono">
                        {call.function}({Object.keys(call.arguments).length} params)
                      </div>
                    ))}
                  </div>
                </details>
              )}
            </div>
          </div>
        ))}

        {/* Loading indicator */}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-4 py-3">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="px-6 py-4 border-t border-gray-200">
        <div className="flex space-x-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about your spending, subscriptions, or goals..."
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isLoading}
          />
          <button
            onClick={sendMessage}
            disabled={isLoading || !input.trim()}
            className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed font-medium"
          >
            Send
          </button>
        </div>

        {/* Example questions */}
        <div className="mt-3 flex flex-wrap gap-2">
          <button
            onClick={() => setInput("How much did I spend on dining last month?")}
            className="text-xs px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded-full text-gray-700 transition-colors"
            disabled={isLoading}
          >
            Dining spending last month
          </button>
          <button
            onClick={() => setInput("What are my top 5 spending categories?")}
            className="text-xs px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded-full text-gray-700 transition-colors"
            disabled={isLoading}
          >
            Top spending categories
          </button>
          <button
            onClick={() => setInput("Show me my subscriptions")}
            className="text-xs px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded-full text-gray-700 transition-colors"
            disabled={isLoading}
          >
            My subscriptions
          </button>
        </div>
      </div>
    </div>
  );
};

export default NLCoach;
