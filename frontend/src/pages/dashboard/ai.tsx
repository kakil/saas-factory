import React, { useState } from 'react';
import { 
  TextGenerator, 
  ChatInterface, 
  CodeGenerator, 
  UsageStats 
} from '../../features/ai/components';
import { ProtectedRoute } from '../../features/auth/components';
import { AuthProvider } from '../../features/auth/hooks';
import { DashboardLayout } from '../../components/layout';

// Define tab types
type TabType = 'text' | 'chat' | 'code' | 'usage';

const AIPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('text');

  return (
    <AuthProvider>
      <ProtectedRoute>
        <DashboardLayout>
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <h1 className="text-2xl font-semibold text-gray-900 mb-6">AI Capabilities</h1>
        
        {/* Tabs */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('text')}
              className={`${
                activeTab === 'text'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm`}
            >
              Text Generation
            </button>
            <button
              onClick={() => setActiveTab('chat')}
              className={`${
                activeTab === 'chat'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm`}
            >
              Chat
            </button>
            <button
              onClick={() => setActiveTab('code')}
              className={`${
                activeTab === 'code'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm`}
            >
              Code Generation
            </button>
            <button
              onClick={() => setActiveTab('usage')}
              className={`${
                activeTab === 'usage'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm`}
            >
              Usage Statistics
            </button>
          </nav>
        </div>
        
        {/* Tab Content */}
        <div className="mt-6">
          {activeTab === 'text' && (
            <div className="max-w-3xl mx-auto">
              <div className="bg-white shadow rounded-lg p-6">
                <h2 className="text-lg font-medium text-gray-900 mb-4">Text Generation</h2>
                <TextGenerator />
              </div>
            </div>
          )}
          
          {activeTab === 'chat' && (
            <div className="max-w-3xl mx-auto">
              <div className="bg-white shadow rounded-lg p-6 h-[600px] flex flex-col">
                <h2 className="text-lg font-medium text-gray-900 mb-4">AI Chat</h2>
                <div className="flex-1 overflow-hidden">
                  <ChatInterface
                    initialMessages={[
                      {
                        role: 'system',
                        content: 'You are a helpful assistant that provides concise, accurate answers.'
                      },
                      {
                        role: 'assistant',
                        content: 'Hello! I\'m your AI assistant. How can I help you today?'
                      }
                    ]}
                  />
                </div>
              </div>
            </div>
          )}
          
          {activeTab === 'code' && (
            <div className="max-w-3xl mx-auto">
              <div className="bg-white shadow rounded-lg p-6">
                <h2 className="text-lg font-medium text-gray-900 mb-4">Code Generation</h2>
                <CodeGenerator />
              </div>
            </div>
          )}
          
          {activeTab === 'usage' && (
            <div className="max-w-3xl mx-auto">
              <UsageStats autoRefresh={false} />
            </div>
          )}
        </div>
          </div>
        </DashboardLayout>
      </ProtectedRoute>
    </AuthProvider>
  );
};

export default AIPage;