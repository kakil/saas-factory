import React, { useState, useCallback } from 'react';
import { useAIGeneration } from '../hooks';
import { PromptRequest } from '../api';

interface TextGeneratorProps {
  defaultModel?: string;
  defaultWorkflow?: string;
  defaultTemperature?: number;
  defaultMaxTokens?: number;
  onGenerate?: (response: string) => void;
  className?: string;
}

export const TextGenerator: React.FC<TextGeneratorProps> = ({
  defaultModel,
  defaultWorkflow = 'general',
  defaultTemperature = 0.7,
  defaultMaxTokens = 1000,
  onGenerate,
  className,
}) => {
  const [prompt, setPrompt] = useState('');
  const [generatedText, setGeneratedText] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [model, setModel] = useState(defaultModel || '');
  const [temperature, setTemperature] = useState(defaultTemperature);
  const [maxTokens, setMaxTokens] = useState(defaultMaxTokens);
  const [workflow, setWorkflow] = useState(defaultWorkflow);

  const { generateFromPrompt, isLoading, error, response } = useAIGeneration({
    onSuccess: (response) => {
      setGeneratedText(response.content);
      onGenerate?.(response.content);
    },
  });

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;
    
    const request: PromptRequest = {
      prompt: prompt.trim(),
      temperature,
      max_tokens: maxTokens,
      workflow,
    };
    
    if (model) {
      request.model = model;
    }
    
    await generateFromPrompt(request);
  }, [prompt, model, temperature, maxTokens, workflow, generateFromPrompt]);

  return (
    <div className={className}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="prompt" className="block text-sm font-medium text-gray-700">
            Prompt
          </label>
          <textarea
            id="prompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            rows={3}
            placeholder="Enter your prompt here..."
            required
          />
        </div>
        
        <div>
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-sm text-indigo-600 hover:text-indigo-800"
          >
            {showAdvanced ? 'Hide' : 'Show'} Advanced Options
          </button>
        </div>
        
        {showAdvanced && (
          <div className="space-y-4 p-4 bg-gray-50 rounded-md">
            <div>
              <label htmlFor="model" className="block text-sm font-medium text-gray-700">
                Model
              </label>
              <input
                type="text"
                id="model"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                placeholder="Optional: Specific model to use"
              />
            </div>
            
            <div>
              <label htmlFor="temperature" className="block text-sm font-medium text-gray-700">
                Temperature: {temperature}
              </label>
              <input
                type="range"
                id="temperature"
                min="0"
                max="1"
                step="0.01"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                className="mt-1 block w-full"
              />
            </div>
            
            <div>
              <label htmlFor="maxTokens" className="block text-sm font-medium text-gray-700">
                Max Tokens: {maxTokens}
              </label>
              <input
                type="range"
                id="maxTokens"
                min="100"
                max="4000"
                step="100"
                value={maxTokens}
                onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                className="mt-1 block w-full"
              />
            </div>
            
            <div>
              <label htmlFor="workflow" className="block text-sm font-medium text-gray-700">
                Workflow
              </label>
              <select
                id="workflow"
                value={workflow}
                onChange={(e) => setWorkflow(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              >
                <option value="general">General</option>
                <option value="code_generation">Code Generation</option>
                <option value="content_generation">Content Generation</option>
              </select>
            </div>
          </div>
        )}
        
        <div>
          <button
            type="submit"
            disabled={isLoading || !prompt.trim()}
            className={`inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white ${
              isLoading ? 'bg-indigo-300' : 'bg-indigo-600 hover:bg-indigo-700'
            } focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500`}
          >
            {isLoading ? 'Generating...' : 'Generate'}
          </button>
        </div>
      </form>
      
      {error && (
        <div className="mt-4 p-4 bg-red-50 text-red-800 rounded-md">
          <h3 className="text-sm font-medium">Error</h3>
          <p className="text-sm">{error.message}</p>
        </div>
      )}
      
      {generatedText && (
        <div className="mt-4">
          <h3 className="text-sm font-medium text-gray-700">Generated Text</h3>
          <div className="mt-1 p-4 bg-gray-50 rounded-md">
            <div className="whitespace-pre-wrap">{generatedText}</div>
          </div>
          
          {response?.usage && (
            <div className="mt-2 text-xs text-gray-500">
              Tokens: {response.usage.estimated_tokens || 'Unknown'} | 
              Model: {response.model_used || 'Default'} | 
              Workflow: {response.workflow_used || 'Default'}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TextGenerator;