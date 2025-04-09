import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useAIChat } from '../hooks';
import { AIMessage, ChatRequest } from '../api';

interface ChatInterfaceProps {
  defaultModel?: string;
  defaultWorkflow?: string;
  defaultTemperature?: number;
  defaultMaxTokens?: number;
  initialMessages?: AIMessage[];
  onMessageSent?: (message: AIMessage) => void;
  onMessageReceived?: (message: AIMessage) => void;
  className?: string;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  defaultModel,
  defaultWorkflow = 'general',
  defaultTemperature = 0.7,
  defaultMaxTokens = 1000,
  initialMessages = [],
  onMessageSent,
  onMessageReceived,
  className,
}) => {
  const [messages, setMessages] = useState<AIMessage[]>(initialMessages);
  const [inputText, setInputText] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [model, setModel] = useState(defaultModel || '');
  const [temperature, setTemperature] = useState(defaultTemperature);
  const [maxTokens, setMaxTokens] = useState(defaultMaxTokens);
  const [workflow, setWorkflow] = useState(defaultWorkflow);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const { generateFromChat, isLoading, error } = useAIChat({
    onSuccess: (response) => {
      const assistantMessage: AIMessage = {
        role: 'assistant',
        content: response.content,
      };
      setMessages((prev) => [...prev, assistantMessage]);
      onMessageReceived?.(assistantMessage);
    },
  });
  
  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;
    
    const userMessage: AIMessage = {
      role: 'user',
      content: inputText.trim(),
    };
    
    setMessages((prev) => [...prev, userMessage]);
    onMessageSent?.(userMessage);
    setInputText('');
    
    // Create full message history
    const allMessages: AIMessage[] = [
      // Add system message if not present
      ...(!messages.some(m => m.role === 'system') ? [{
        role: 'system',
        content: 'You are a helpful assistant.',
      }] : []),
      ...messages,
      userMessage,
    ];
    
    const request: ChatRequest = {
      messages: allMessages,
      temperature,
      max_tokens: maxTokens,
      workflow,
    };
    
    if (model) {
      request.model = model;
    }
    
    await generateFromChat(request);
  }, [inputText, messages, model, temperature, maxTokens, workflow, generateFromChat, onMessageSent]);
  
  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  return (
    <div className={`flex flex-col h-full ${className}`}>
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 my-8">
            No messages yet. Start a conversation!
          </div>
        )}
        
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-3/4 px-4 py-2 rounded-lg ${
                message.role === 'user'
                  ? 'bg-indigo-100 text-indigo-900'
                  : message.role === 'system'
                  ? 'bg-gray-100 text-gray-800 italic'
                  : 'bg-white border border-gray-200 text-gray-900'
              }`}
            >
              <div className="text-xs text-gray-500 mb-1">
                {message.role === 'user'
                  ? 'You'
                  : message.role === 'system'
                  ? 'System'
                  : 'AI Assistant'}
              </div>
              <div className="whitespace-pre-wrap">{message.content}</div>
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="max-w-3/4 px-4 py-2 bg-white border border-gray-200 rounded-lg text-gray-500">
              <div className="text-xs mb-1">AI Assistant</div>
              <div className="flex space-x-1">
                <div className="animate-bounce">●</div>
                <div className="animate-bounce" style={{ animationDelay: '0.2s' }}>●</div>
                <div className="animate-bounce" style={{ animationDelay: '0.4s' }}>●</div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {error && (
        <div className="p-2 mb-2 bg-red-50 text-red-800 rounded-md mx-4">
          <p className="text-sm">{error.message}</p>
        </div>
      )}
      
      <div className="p-4">
        <div>
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-xs text-indigo-600 hover:text-indigo-800 mb-2"
          >
            {showAdvanced ? 'Hide' : 'Show'} Advanced Options
          </button>
        </div>
        
        {showAdvanced && (
          <div className="mb-4 p-3 bg-gray-50 rounded-md space-y-3">
            <div>
              <label htmlFor="chat-model" className="block text-xs font-medium text-gray-700">
                Model
              </label>
              <input
                type="text"
                id="chat-model"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-xs"
                placeholder="Optional: Specific model to use"
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="chat-temperature" className="block text-xs font-medium text-gray-700">
                  Temperature: {temperature}
                </label>
                <input
                  type="range"
                  id="chat-temperature"
                  min="0"
                  max="1"
                  step="0.01"
                  value={temperature}
                  onChange={(e) => setTemperature(parseFloat(e.target.value))}
                  className="mt-1 block w-full"
                />
              </div>
              
              <div>
                <label htmlFor="chat-maxTokens" className="block text-xs font-medium text-gray-700">
                  Max Tokens: {maxTokens}
                </label>
                <input
                  type="range"
                  id="chat-maxTokens"
                  min="100"
                  max="4000"
                  step="100"
                  value={maxTokens}
                  onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                  className="mt-1 block w-full"
                />
              </div>
            </div>
            
            <div>
              <label htmlFor="chat-workflow" className="block text-xs font-medium text-gray-700">
                Workflow
              </label>
              <select
                id="chat-workflow"
                value={workflow}
                onChange={(e) => setWorkflow(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-xs"
              >
                <option value="general">General</option>
                <option value="code_generation">Code Generation</option>
                <option value="content_generation">Content Generation</option>
              </select>
            </div>
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="flex">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            className="flex-1 rounded-l-md border-gray-300 focus:border-indigo-500 focus:ring-indigo-500"
            placeholder="Type your message..."
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !inputText.trim()}
            className={`px-4 py-2 rounded-r-md ${
              isLoading || !inputText.trim()
                ? 'bg-indigo-300 text-white'
                : 'bg-indigo-600 text-white hover:bg-indigo-700'
            }`}
          >
            {isLoading ? 'Sending...' : 'Send'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatInterface;