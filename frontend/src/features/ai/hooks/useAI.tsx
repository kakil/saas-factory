import { useState, useCallback } from 'react';
import aiClient, {
  PromptRequest,
  ChatRequest,
  CodeGenerationRequest,
  ContentGenerationRequest,
  EmbeddingRequest,
  AIResponse,
  EmbeddingResponse,
  AIApiError,
  AsyncTaskResponse,
  AsyncTaskStatusResponse
} from '../api/ai-client';

interface AIHookState {
  loading: boolean;
  error: AIApiError | Error | null;
  response: AIResponse | null;
}

interface AsyncAIHookState {
  submitting: boolean;
  polling: boolean;
  taskId: string | null;
  status: string | null;
  error: AIApiError | Error | null;
  response: any | null;
}

interface UseAIOptions {
  onSuccess?: (response: AIResponse) => void;
  onError?: (error: AIApiError | Error) => void;
}

interface UseAsyncAIOptions {
  onSuccess?: (response: any) => void;
  onError?: (error: AIApiError | Error) => void;
  pollInterval?: number; // In milliseconds
  autoPoll?: boolean;
}

/**
 * Hook for generating text using AI
 */
export const useAIGeneration = (options?: UseAIOptions) => {
  const [state, setState] = useState<AIHookState>({
    loading: false,
    error: null,
    response: null,
  });

  const generateFromPrompt = useCallback(
    async (request: PromptRequest) => {
      setState((prev) => ({ ...prev, loading: true, error: null }));
      try {
        const response = await aiClient.generateFromPrompt(request);
        setState({ loading: false, error: null, response });
        options?.onSuccess?.(response);
        return response;
      } catch (error) {
        const errorObj = error instanceof AIApiError ? error : new Error(String(error));
        setState({ loading: false, error: errorObj, response: null });
        options?.onError?.(errorObj);
        throw error;
      }
    },
    [options]
  );

  return {
    generateFromPrompt,
    isLoading: state.loading,
    error: state.error,
    response: state.response,
    reset: () => setState({ loading: false, error: null, response: null }),
  };
};

/**
 * Hook for AI chat completion
 */
export const useAIChat = (options?: UseAIOptions) => {
  const [state, setState] = useState<AIHookState>({
    loading: false,
    error: null,
    response: null,
  });

  const generateFromChat = useCallback(
    async (request: ChatRequest) => {
      setState((prev) => ({ ...prev, loading: true, error: null }));
      try {
        const response = await aiClient.generateFromChat(request);
        setState({ loading: false, error: null, response });
        options?.onSuccess?.(response);
        return response;
      } catch (error) {
        const errorObj = error instanceof AIApiError ? error : new Error(String(error));
        setState({ loading: false, error: errorObj, response: null });
        options?.onError?.(errorObj);
        throw error;
      }
    },
    [options]
  );

  return {
    generateFromChat,
    isLoading: state.loading,
    error: state.error,
    response: state.response,
    reset: () => setState({ loading: false, error: null, response: null }),
  };
};

/**
 * Hook for AI code generation
 */
export const useAICodeGeneration = (options?: UseAIOptions) => {
  const [state, setState] = useState<AIHookState>({
    loading: false,
    error: null,
    response: null,
  });

  const generateCode = useCallback(
    async (request: CodeGenerationRequest) => {
      setState((prev) => ({ ...prev, loading: true, error: null }));
      try {
        const response = await aiClient.generateCode(request);
        setState({ loading: false, error: null, response });
        options?.onSuccess?.(response);
        return response;
      } catch (error) {
        const errorObj = error instanceof AIApiError ? error : new Error(String(error));
        setState({ loading: false, error: errorObj, response: null });
        options?.onError?.(errorObj);
        throw error;
      }
    },
    [options]
  );

  return {
    generateCode,
    isLoading: state.loading,
    error: state.error,
    response: state.response,
    reset: () => setState({ loading: false, error: null, response: null }),
  };
};

/**
 * Hook for AI content generation (marketing, blog posts, etc.)
 */
export const useAIContentGeneration = (options?: UseAIOptions) => {
  const [state, setState] = useState<AIHookState>({
    loading: false,
    error: null,
    response: null,
  });

  const generateContent = useCallback(
    async (request: ContentGenerationRequest) => {
      setState((prev) => ({ ...prev, loading: true, error: null }));
      try {
        const response = await aiClient.generateContent(request);
        setState({ loading: false, error: null, response });
        options?.onSuccess?.(response);
        return response;
      } catch (error) {
        const errorObj = error instanceof AIApiError ? error : new Error(String(error));
        setState({ loading: false, error: errorObj, response: null });
        options?.onError?.(errorObj);
        throw error;
      }
    },
    [options]
  );

  return {
    generateContent,
    isLoading: state.loading,
    error: state.error,
    response: state.response,
    reset: () => setState({ loading: false, error: null, response: null }),
  };
};

/**
 * Hook for async AI operations with optional polling
 */
export const useAsyncAI = (options?: UseAsyncAIOptions) => {
  const {
    onSuccess,
    onError,
    pollInterval = 2000, // Default poll every 2 seconds
    autoPoll = true,
  } = options || {};

  const [state, setState] = useState<AsyncAIHookState>({
    submitting: false,
    polling: false,
    taskId: null,
    status: null,
    error: null,
    response: null,
  });

  // Submit async prompt request
  const submitAsyncPrompt = useCallback(
    async (request: PromptRequest, callbackUrl?: string) => {
      setState((prev) => ({ ...prev, submitting: true, error: null }));
      try {
        const response = await aiClient.submitAsyncPrompt(request, callbackUrl);
        const newState = {
          submitting: false,
          polling: autoPoll,
          taskId: response.task_id,
          status: response.status,
          error: null,
          response: null,
        };
        setState(newState);
        
        // Start polling if autoPoll is enabled
        if (autoPoll && response.task_id) {
          pollTaskStatus(response.task_id);
        }
        
        return response;
      } catch (error) {
        const errorObj = error instanceof AIApiError ? error : new Error(String(error));
        setState({
          submitting: false,
          polling: false,
          taskId: null,
          status: null,
          error: errorObj,
          response: null,
        });
        options?.onError?.(errorObj);
        throw error;
      }
    },
    [autoPoll, options]
  );

  // Submit async chat request
  const submitAsyncChat = useCallback(
    async (request: ChatRequest, callbackUrl?: string) => {
      setState((prev) => ({ ...prev, submitting: true, error: null }));
      try {
        const response = await aiClient.submitAsyncChat(request, callbackUrl);
        const newState = {
          submitting: false,
          polling: autoPoll,
          taskId: response.task_id,
          status: response.status,
          error: null,
          response: null,
        };
        setState(newState);
        
        // Start polling if autoPoll is enabled
        if (autoPoll && response.task_id) {
          pollTaskStatus(response.task_id);
        }
        
        return response;
      } catch (error) {
        const errorObj = error instanceof AIApiError ? error : new Error(String(error));
        setState({
          submitting: false,
          polling: false,
          taskId: null,
          status: null,
          error: errorObj,
          response: null,
        });
        options?.onError?.(errorObj);
        throw error;
      }
    },
    [autoPoll, options]
  );

  // Submit async code generation request
  const submitAsyncCodeGeneration = useCallback(
    async (request: CodeGenerationRequest, callbackUrl?: string) => {
      setState((prev) => ({ ...prev, submitting: true, error: null }));
      try {
        const response = await aiClient.submitAsyncCodeGeneration(request, callbackUrl);
        const newState = {
          submitting: false,
          polling: autoPoll,
          taskId: response.task_id,
          status: response.status,
          error: null,
          response: null,
        };
        setState(newState);
        
        // Start polling if autoPoll is enabled
        if (autoPoll && response.task_id) {
          pollTaskStatus(response.task_id);
        }
        
        return response;
      } catch (error) {
        const errorObj = error instanceof AIApiError ? error : new Error(String(error));
        setState({
          submitting: false,
          polling: false,
          taskId: null,
          status: null,
          error: errorObj,
          response: null,
        });
        options?.onError?.(errorObj);
        throw error;
      }
    },
    [autoPoll, options]
  );

  // Poll for task status
  const pollTaskStatus = useCallback(
    async (taskId: string) => {
      if (!taskId) return;

      setState((prev) => ({ ...prev, polling: true }));
      
      try {
        const statusResponse = await aiClient.getTaskStatus(taskId);
        
        // Update state with current status
        setState((prev) => ({
          ...prev,
          status: statusResponse.status,
          // Only stop polling if the task is completed or failed
          polling: !['completed', 'failed'].includes(statusResponse.status),
        }));
        
        // If task is completed, get the result
        if (statusResponse.status === 'completed') {
          try {
            const resultResponse = await aiClient.getTaskResult(taskId);
            setState((prev) => ({
              ...prev,
              response: resultResponse,
              polling: false,
            }));
            
            // Call onSuccess callback
            onSuccess?.(resultResponse);
            
          } catch (resultError) {
            // Handle result retrieval error
            const errorObj = resultError instanceof AIApiError ? resultError : new Error(String(resultError));
            setState((prev) => ({
              ...prev,
              error: errorObj,
              polling: false,
            }));
            onError?.(errorObj);
          }
        }
        
        // If task is still in progress, continue polling
        if (['pending', 'processing'].includes(statusResponse.status)) {
          setTimeout(() => pollTaskStatus(taskId), pollInterval);
        }
        
        // If task failed, update error state
        if (statusResponse.status === 'failed') {
          const errorMessage = statusResponse.message || 'Task processing failed';
          const errorObj = new Error(errorMessage);
          setState((prev) => ({
            ...prev,
            error: errorObj,
            polling: false,
          }));
          onError?.(errorObj);
        }
        
        return statusResponse;
      } catch (error) {
        // Handle polling error
        const errorObj = error instanceof AIApiError ? error : new Error(String(error));
        setState((prev) => ({
          ...prev,
          error: errorObj,
          polling: false,
        }));
        onError?.(errorObj);
        throw error;
      }
    },
    [pollInterval, onSuccess, onError]
  );

  // Start/stop polling manually
  const startPolling = useCallback(() => {
    if (state.taskId && !state.polling) {
      setState((prev) => ({ ...prev, polling: true }));
      pollTaskStatus(state.taskId);
    }
  }, [state.taskId, state.polling, pollTaskStatus]);

  const stopPolling = useCallback(() => {
    setState((prev) => ({ ...prev, polling: false }));
  }, []);

  // Check task status manually (one-time check)
  const checkTaskStatus = useCallback(async (taskId: string) => {
    try {
      const response = await aiClient.getTaskStatus(taskId);
      setState((prev) => ({
        ...prev,
        taskId,
        status: response.status,
      }));
      return response;
    } catch (error) {
      const errorObj = error instanceof AIApiError ? error : new Error(String(error));
      setState((prev) => ({
        ...prev,
        error: errorObj,
      }));
      throw error;
    }
  }, []);

  // Get task result manually
  const getTaskResult = useCallback(async (taskId: string) => {
    try {
      const response = await aiClient.getTaskResult(taskId);
      setState((prev) => ({
        ...prev,
        taskId,
        response,
      }));
      return response;
    } catch (error) {
      const errorObj = error instanceof AIApiError ? error : new Error(String(error));
      setState((prev) => ({
        ...prev,
        error: errorObj,
      }));
      throw error;
    }
  }, []);

  return {
    submitAsyncPrompt,
    submitAsyncChat,
    submitAsyncCodeGeneration,
    checkTaskStatus,
    getTaskResult,
    startPolling,
    stopPolling,
    isSubmitting: state.submitting,
    isPolling: state.polling,
    taskId: state.taskId,
    status: state.status,
    response: state.response,
    error: state.error,
    reset: () => setState({
      submitting: false,
      polling: false,
      taskId: null,
      status: null,
      error: null,
      response: null,
    }),
  };
};

/**
 * Hook for fetching AI usage statistics
 */
export const useAIUsageStats = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<AIApiError | Error | null>(null);
  const [stats, setStats] = useState<any>(null);

  const getUsageStats = useCallback(async (timeframe: 'day' | 'week' | 'month' = 'day') => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await aiClient.getUsageStatistics(timeframe);
      setStats(response);
      setLoading(false);
      return response;
    } catch (error) {
      const errorObj = error instanceof AIApiError ? error : new Error(String(error));
      setError(errorObj);
      setLoading(false);
      throw error;
    }
  }, []);

  return {
    getUsageStats,
    isLoading: loading,
    error,
    stats,
    reset: () => {
      setLoading(false);
      setError(null);
      setStats(null);
    },
  };
};

/**
 * Main hook combining all AI features
 */
export const useAI = () => {
  // Get available workflows
  const [workflowsLoading, setWorkflowsLoading] = useState(false);
  const [workflowsError, setWorkflowsError] = useState<AIApiError | Error | null>(null);
  const [workflows, setWorkflows] = useState<string[]>([]);

  const getWorkflows = useCallback(async () => {
    setWorkflowsLoading(true);
    setWorkflowsError(null);
    
    try {
      const response = await aiClient.getAvailableWorkflows();
      setWorkflows(response);
      setWorkflowsLoading(false);
      return response;
    } catch (error) {
      const errorObj = error instanceof AIApiError ? error : new Error(String(error));
      setWorkflowsError(errorObj);
      setWorkflowsLoading(false);
      throw error;
    }
  }, []);

  // Combine all AI hooks
  const textGeneration = useAIGeneration();
  const chatGeneration = useAIChat();
  const codeGeneration = useAICodeGeneration();
  const contentGeneration = useAIContentGeneration();
  const asyncAI = useAsyncAI();
  const usageStats = useAIUsageStats();

  return {
    // Workflows
    getWorkflows,
    workflows,
    workflowsLoading,
    workflowsError,
    
    // Direct AI operations
    generateFromPrompt: textGeneration.generateFromPrompt,
    generateFromChat: chatGeneration.generateFromChat,
    generateCode: codeGeneration.generateCode,
    generateContent: contentGeneration.generateContent,
    
    // Async operations
    submitAsyncPrompt: asyncAI.submitAsyncPrompt,
    submitAsyncChat: asyncAI.submitAsyncChat,
    submitAsyncCodeGeneration: asyncAI.submitAsyncCodeGeneration,
    checkTaskStatus: asyncAI.checkTaskStatus,
    getTaskResult: asyncAI.getTaskResult,
    
    // Usage statistics
    getUsageStats: usageStats.getUsageStats,
    
    // Additional hooks for more specific use cases
    hooks: {
      useAIGeneration,
      useAIChat,
      useAICodeGeneration,
      useAIContentGeneration,
      useAsyncAI,
      useAIUsageStats,
    },
    
    // Direct access to the client
    client: aiClient,
  };
};