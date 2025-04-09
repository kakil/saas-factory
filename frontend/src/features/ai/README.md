# AI Feature Module

This module provides AI capabilities to the SaaS Factory, including text generation, chat, code generation, content creation, and embeddings. It communicates with the backend AI service which uses WilmerAI for orchestration.

## Architecture

The AI feature module follows a layered architecture:

1. **API Layer** - Client for communicating with backend AI endpoints
2. **Hooks Layer** - React hooks providing AI functionality
3. **Components Layer** - Reusable UI components
4. **Utils Layer** - Helper functions and utilities

## Components

- `TextGenerator` - Simple interface for text generation
- `ChatInterface` - Chat interface with conversation history
- `CodeGenerator` - Code generation with language selection
- `UsageStats` - Statistics and usage metrics
- `AsyncTaskManager` - Manages long-running AI tasks

## Hooks

- `useAI` - Main hook providing all AI capabilities
- `useAIGeneration` - Hook for text generation
- `useAIChat` - Hook for chat interactions
- `useAICodeGeneration` - Hook for code generation
- `useAIContentGeneration` - Hook for marketing content
- `useAsyncAI` - Hook for async AI operations
- `useAIUsageStats` - Hook for usage statistics

## API Client

The `AIClient` provides a clean interface to the backend AI service, with:

- Synchronous operations (generate, chat, code, content)
- Asynchronous operations with polling
- Usage statistics and workflow management
- Error handling

## Usage

```tsx
import { useAI } from '@features/ai';

const MyComponent = () => {
  const { generateFromPrompt, isLoading, response } = useAI();

  const handleSubmit = async () => {
    await generateFromPrompt({
      prompt: 'Explain how AI works',
      temperature: 0.7,
    });
  };

  return (
    <div>
      <button onClick={handleSubmit} disabled={isLoading}>Generate</button>
      {response && <div>{response.content}</div>}
    </div>
  );
};
```

## Models

WilmerAI provides access to multiple AI models:

- `gemini-pro` - Google's Gemini Pro model (default)
- `gpt-3.5-turbo` - OpenAI's GPT 3.5 model
- `claude-3` - Anthropic's Claude model
- `deepseek-coder` - DeepSeek's specialized coding model

## Workflows

The system supports specialized workflows:

- `general` - Default workflow for standard queries
- `code_generation` - Optimized for generating code
- `content_generation` - Specialized for marketing content

## Async Operations

For long-running tasks, use the async capabilities:

```tsx
const { submitAsyncPrompt, status, response } = useAsyncAI();

await submitAsyncPrompt({
  prompt: 'Generate a long essay about AI',
  max_tokens: 4000
});

// The status will update automatically through polling
// When complete, response will contain the result
```