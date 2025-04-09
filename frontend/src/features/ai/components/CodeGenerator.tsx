import React, { useState, useCallback } from 'react';
import { useAICodeGeneration } from '../hooks';
import { CodeGenerationRequest } from '../api';

interface CodeGeneratorProps {
  defaultModel?: string;
  defaultTemperature?: number;
  onGenerate?: (code: string) => void;
  className?: string;
}

export const CodeGenerator: React.FC<CodeGeneratorProps> = ({
  defaultModel,
  defaultTemperature = 0.2, // Lower temperature works better for code
  onGenerate,
  className,
}) => {
  const [prompt, setPrompt] = useState('');
  const [language, setLanguage] = useState('');
  const [contextCode, setContextCode] = useState('');
  const [generatedCode, setGeneratedCode] = useState('');
  const [model, setModel] = useState(defaultModel || '');
  const [temperature, setTemperature] = useState(defaultTemperature);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const { generateCode, isLoading, error, response } = useAICodeGeneration({
    onSuccess: (response) => {
      setGeneratedCode(response.content);
      onGenerate?.(response.content);
    },
  });

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;
    
    const request: CodeGenerationRequest = {
      prompt: prompt.trim(),
      language: language.trim() || undefined,
      code_context: contextCode.trim() || undefined,
      temperature,
    };
    
    if (model) {
      request.model = model;
    }
    
    await generateCode(request);
  }, [prompt, language, contextCode, model, temperature, generateCode]);

  // Common programming languages
  const languages = [
    'Python',
    'JavaScript',
    'TypeScript',
    'Java',
    'C#',
    'C++',
    'PHP',
    'Ruby',
    'Go',
    'Rust',
    'Swift',
    'Kotlin',
    'SQL',
    'HTML',
    'CSS',
    'Shell',
  ];

  return (
    <div className={className}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="prompt" className="block text-sm font-medium text-gray-700">
            What code would you like to generate?
          </label>
          <textarea
            id="prompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            rows={3}
            placeholder="E.g., Write a function that sorts an array of objects by a specific property"
            required
          />
        </div>
        
        <div>
          <label htmlFor="language" className="block text-sm font-medium text-gray-700">
            Programming Language
          </label>
          <select
            id="language"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          >
            <option value="">Select a language (optional)</option>
            {languages.map((lang) => (
              <option key={lang} value={lang}>
                {lang}
              </option>
            ))}
          </select>
        </div>
        
        <div>
          <label htmlFor="contextCode" className="block text-sm font-medium text-gray-700">
            Context or Existing Code (optional)
          </label>
          <textarea
            id="contextCode"
            value={contextCode}
            onChange={(e) => setContextCode(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm font-mono"
            rows={5}
            placeholder="Paste existing code or context here to help the AI understand your requirements"
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
              <p className="mt-1 text-xs text-gray-500">
                Lower values produce more deterministic code. Higher values can be more creative but less accurate.
              </p>
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
            {isLoading ? 'Generating Code...' : 'Generate Code'}
          </button>
        </div>
      </form>
      
      {error && (
        <div className="mt-4 p-4 bg-red-50 text-red-800 rounded-md">
          <h3 className="text-sm font-medium">Error</h3>
          <p className="text-sm">{error.message}</p>
        </div>
      )}
      
      {generatedCode && (
        <div className="mt-4">
          <div className="flex justify-between items-center">
            <h3 className="text-sm font-medium text-gray-700">Generated Code</h3>
            <button
              onClick={() => {
                navigator.clipboard.writeText(generatedCode);
              }}
              className="text-xs text-indigo-600 hover:text-indigo-800"
            >
              Copy to Clipboard
            </button>
          </div>
          <div className="mt-1 p-4 bg-gray-50 rounded-md">
            <pre className="overflow-auto text-sm font-mono whitespace-pre">
              {generatedCode}
            </pre>
          </div>
          
          {response?.usage && (
            <div className="mt-2 text-xs text-gray-500">
              Tokens: {response.usage.estimated_tokens || 'Unknown'} | 
              Model: {response.model_used || 'Default'}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default CodeGenerator;