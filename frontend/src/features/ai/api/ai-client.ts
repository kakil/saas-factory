import axios, { AxiosError, AxiosInstance, AxiosResponse } from 'axios';

// Define types for API requests and responses
export interface AIMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface PromptRequest {
  prompt: string;
  model?: string;
  temperature?: number;
  max_tokens?: number;
  workflow?: string;
  system_prompt?: string;
}

export interface ChatRequest {
  messages: AIMessage[];
  model?: string;
  temperature?: number;
  max_tokens?: number;
  workflow?: string;
}

export interface CodeGenerationRequest {
  prompt: string;
  language?: string;
  code_context?: string;
  model?: string;
  temperature?: number;
}

export interface ContentGenerationRequest {
  topic: string;
  content_type: 'blog' | 'email' | 'social' | 'ad';
  tone?: string;
  word_count?: number;
  target_audience?: string;
  model?: string;
  temperature?: number;
}

export interface EmbeddingRequest {
  text: string;
  model?: string;
}

export interface AIResponse {
  content: string;
  model_used: string;
  workflow_used?: string;
  usage?: {
    estimated_tokens?: number;
    prompt_tokens?: number;
    completion_tokens?: number;
    input_tokens?: number;
  };
}

export interface EmbeddingResponse {
  embedding: number[];
  model_used: string;
  dimension: number;
  usage?: {
    estimated_tokens?: number;
    input_tokens?: number;
  };
}

export interface AsyncTaskResponse {
  task_id: string;
  status: string;
  message?: string;
}

export interface AsyncTaskStatusResponse {
  task_id: string;
  status: string;
  result?: any;
  message?: string;
  created_at?: number;
  completed_at?: number;
}

export interface UsageStatistics {
  timeframe: string;
  period_start: string;
  period_end: string;
  user?: {
    id: number;
    stats: {
      total_requests: number;
      total_tokens: number;
      daily_breakdown: Record<string, { requests: number; tokens: number }>;
    };
  };
  tenant?: {
    id: number;
    stats: {
      total_requests: number;
      total_tokens: number;
      daily_breakdown: Record<string, { requests: number; tokens: number }>;
    };
  };
}

export class AIApiError extends Error {
  public readonly statusCode: number;
  public readonly errorDetails: any;

  constructor(message: string, statusCode: number, errorDetails?: any) {
    super(message);
    this.name = 'AIApiError';
    this.statusCode = statusCode;
    this.errorDetails = errorDetails;
  }
}

// Constants
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_VERSION = '/api/v1';

export class AIClient {
  private api: AxiosInstance;
  private baseUrl: string;

  constructor(baseUrl = `${API_URL}${API_VERSION}`) {
    this.baseUrl = baseUrl;
    this.api = axios.create({
      baseURL: baseUrl,
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true,
    });
    
    // Add auth token to requests
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );
  }

  private handleError(error: any): never {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError;
      const statusCode = axiosError.response?.status || 500;
      const errorMessage =
        axiosError.response?.data?.detail ||
        axiosError.message ||
        'An unknown error occurred';
      const errorDetails = axiosError.response?.data;

      throw new AIApiError(errorMessage, statusCode, errorDetails);
    }
    throw error;
  }

  // Synchronous AI endpoints

  async generateFromPrompt(request: PromptRequest): Promise<AIResponse> {
    try {
      const response = await this.api.post<AIResponse>('/ai/generate', request);
      return response.data;
    } catch (error) {
      return this.handleError(error);
    }
  }

  async generateFromChat(request: ChatRequest): Promise<AIResponse> {
    try {
      const response = await this.api.post<AIResponse>('/ai/chat', request);
      return response.data;
    } catch (error) {
      return this.handleError(error);
    }
  }

  async generateCode(request: CodeGenerationRequest): Promise<AIResponse> {
    try {
      const response = await this.api.post<AIResponse>('/ai/code', request);
      return response.data;
    } catch (error) {
      return this.handleError(error);
    }
  }

  async generateContent(request: ContentGenerationRequest): Promise<AIResponse> {
    try {
      const response = await this.api.post<AIResponse>('/ai/content', request);
      return response.data;
    } catch (error) {
      return this.handleError(error);
    }
  }

  async generateEmbeddings(request: EmbeddingRequest): Promise<EmbeddingResponse> {
    try {
      const response = await this.api.post<EmbeddingResponse>('/ai/embeddings', request);
      return response.data;
    } catch (error) {
      return this.handleError(error);
    }
  }

  async getAvailableWorkflows(): Promise<string[]> {
    try {
      const response = await this.api.get<string[]>('/ai/workflows');
      return response.data;
    } catch (error) {
      return this.handleError(error);
    }
  }

  // Asynchronous AI endpoints

  async submitAsyncPrompt(
    request: PromptRequest,
    callbackUrl?: string
  ): Promise<AsyncTaskResponse> {
    try {
      let url = '/ai/async/generate';
      if (callbackUrl) {
        url += `?callback_url=${encodeURIComponent(callbackUrl)}`;
      }
      const response = await this.api.post<AsyncTaskResponse>(url, request);
      return response.data;
    } catch (error) {
      return this.handleError(error);
    }
  }

  async submitAsyncChat(
    request: ChatRequest,
    callbackUrl?: string
  ): Promise<AsyncTaskResponse> {
    try {
      let url = '/ai/async/chat';
      if (callbackUrl) {
        url += `?callback_url=${encodeURIComponent(callbackUrl)}`;
      }
      const response = await this.api.post<AsyncTaskResponse>(url, request);
      return response.data;
    } catch (error) {
      return this.handleError(error);
    }
  }

  async submitAsyncCodeGeneration(
    request: CodeGenerationRequest,
    callbackUrl?: string
  ): Promise<AsyncTaskResponse> {
    try {
      let url = '/ai/async/code';
      if (callbackUrl) {
        url += `?callback_url=${encodeURIComponent(callbackUrl)}`;
      }
      const response = await this.api.post<AsyncTaskResponse>(url, request);
      return response.data;
    } catch (error) {
      return this.handleError(error);
    }
  }

  async getTaskStatus(taskId: string): Promise<AsyncTaskStatusResponse> {
    try {
      const response = await this.api.get<AsyncTaskStatusResponse>(`/ai/async/tasks/${taskId}`);
      return response.data;
    } catch (error) {
      return this.handleError(error);
    }
  }

  async getTaskResult(taskId: string): Promise<any> {
    try {
      const response = await this.api.get<any>(`/ai/async/tasks/${taskId}/result`);
      return response.data;
    } catch (error) {
      return this.handleError(error);
    }
  }

  async listAsyncTasks(limit: number = 100): Promise<AsyncTaskStatusResponse[]> {
    try {
      const response = await this.api.get<AsyncTaskStatusResponse[]>(
        `/ai/async/tasks?limit=${limit}`
      );
      return response.data;
    } catch (error) {
      return this.handleError(error);
    }
  }

  // Usage statistics

  async getUsageStatistics(timeframe: 'day' | 'week' | 'month' = 'day'): Promise<UsageStatistics> {
    try {
      const response = await this.api.get<UsageStatistics>(`/ai/usage?timeframe=${timeframe}`);
      return response.data;
    } catch (error) {
      return this.handleError(error);
    }
  }
}

// Export a default instance
const aiClient = new AIClient();
export default aiClient;
