/**
 * Utility functions for AI features
 */

/**
 * Estimate tokens in text using a simple word-based approach
 * Note: This is an approximation. Different tokenizers will give different results.
 * 
 * @param text The text to estimate tokens for
 * @returns Estimated token count
 */
export const estimateTokens = (text: string): number => {
  if (!text || typeof text !== 'string') return 0;
  
  // Very rough approximation: 1 token is about 0.75 words
  const words = text.trim().split(/\s+/).length;
  return Math.ceil(words * 1.3);
};

/**
 * Format code with proper syntax highlighting (using highlight.js or Prism)
 * This is a placeholder for a more complete implementation
 * 
 * @param code The code to format
 * @param language The programming language
 * @returns Formatted code (or original if no formatting available)
 */
export const formatCode = (code: string, language?: string): string => {
  // This would typically use a library like highlight.js or Prism
  // For now, we're just returning the original code
  return code;
};

/**
 * Parse a markdown string to HTML (basic implementation)
 * 
 * @param markdown The markdown string to parse
 * @returns Simple HTML representation
 */
export const parseMarkdown = (markdown: string): string => {
  if (!markdown) return '';
  
  let html = markdown;
  
  // Headers
  html = html.replace(/^# (.*?)$/gm, '<h1>$1</h1>');
  html = html.replace(/^## (.*?)$/gm, '<h2>$1</h2>');
  html = html.replace(/^### (.*?)$/gm, '<h3>$1</h3>');
  
  // Bold and Italic
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
  
  // Lists
  html = html.replace(/^\- (.*?)$/gm, '<li>$1</li>');
  html = html.replace(/<li>(.*?)<\/li>(?:\s*<li>|$)/gs, '<ul><li>$1</li></ul>');
  
  // Code blocks
  html = html.replace(/```(.*?)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
  html = html.replace(/`(.*?)`/g, '<code>$1</code>');
  
  // Paragraphs - wrap content that's not already in HTML tags
  html = html.replace(/(?:^|\n)(?!<[a-z0-9])[^\n]+(?:\n|$)/g, '<p>$&</p>');
  
  // Line breaks
  html = html.replace(/\n/g, '<br>');
  
  return html;
};

/**
 * Calculate price based on token usage
 * 
 * @param tokens Number of tokens used
 * @param modelName Name of the model used
 * @returns Price in USD
 */
export const calculateTokenPrice = (tokens: number, modelName: string): number => {
  // These rates are approximate and should be updated with actual pricing
  const rates: Record<string, number> = {
    'gpt-3.5-turbo': 0.002 / 1000, // $0.002 per 1000 tokens
    'gpt-4': 0.03 / 1000, // $0.03 per 1000 tokens
    'gemini-pro': 0.0010 / 1000, // $0.0010 per 1000 tokens
    'claude-3': 0.015 / 1000, // $0.015 per 1000 tokens
    'default': 0.002 / 1000, // Default rate if model not found
  };
  
  // Get rate for the model or use default
  const rate = rates[modelName.toLowerCase()] || rates.default;
  
  // Calculate price
  return tokens * rate;
};

/**
 * Get readable name for AI model
 * 
 * @param modelId The model ID/name
 * @returns User-friendly model name
 */
export const getModelReadableName = (modelId: string): string => {
  const modelNames: Record<string, string> = {
    'gpt-3.5-turbo': 'GPT-3.5 Turbo',
    'gpt-4': 'GPT-4',
    'gemini-pro': 'Gemini Pro',
    'gemini-pro-vision': 'Gemini Pro Vision',
    'claude-3-opus': 'Claude 3 Opus',
    'claude-3-sonnet': 'Claude 3 Sonnet',
    'claude-3-haiku': 'Claude 3 Haiku',
    'deepseek-coder': 'DeepSeek Coder',
  };
  
  return modelNames[modelId] || modelId;
};

/**
 * Get suggested workflows based on user prompt
 * 
 * @param prompt User prompt
 * @returns List of suggested workflows
 */
export const suggestWorkflows = (prompt: string): string[] => {
  // Simple keyword-based workflow suggestion
  const promptLower = prompt.toLowerCase();
  const suggestions: string[] = [];
  
  // Check for code-related keywords
  if (/\b(code|function|class|program|algorithm|javascript|python|typescript)\b/.test(promptLower)) {
    suggestions.push('code_generation');
  }
  
  // Check for content-related keywords
  if (/\b(blog|article|email|marketing|social media|post|content|write)\b/.test(promptLower)) {
    suggestions.push('content_generation');
  }
  
  // Always add general as a fallback
  if (suggestions.length === 0 || !suggestions.includes('general')) {
    suggestions.push('general');
  }
  
  return suggestions;
};