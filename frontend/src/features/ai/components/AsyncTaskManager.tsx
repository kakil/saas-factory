import React, { useState, useEffect, useCallback } from 'react';
import { useAsyncAI } from '../hooks';
import { AsyncTaskStatusResponse } from '../api';

interface AsyncTaskManagerProps {
  taskId?: string;
  onTaskCompleted?: (result: any) => void;
  onTaskFailed?: (error: Error) => void;
  className?: string;
  autoRefresh?: boolean;
  refreshInterval?: number; // in milliseconds
  showResultPreview?: boolean;
}

export const AsyncTaskManager: React.FC<AsyncTaskManagerProps> = ({
  taskId: initialTaskId,
  onTaskCompleted,
  onTaskFailed,
  className,
  autoRefresh = true,
  refreshInterval = 2000, // 2 seconds
  showResultPreview = true,
}) => {
  const [taskId, setTaskId] = useState<string | null>(initialTaskId || null);
  const {
    checkTaskStatus,
    getTaskResult,
    startPolling,
    stopPolling,
    isPolling,
    status,
    response,
    error,
  } = useAsyncAI({
    pollInterval: refreshInterval,
    autoPoll: autoRefresh && !!initialTaskId,
    onSuccess: (result) => {
      onTaskCompleted?.(result);
    },
    onError: (error) => {
      onTaskFailed?.(error);
    },
  });

  // If initialTaskId changes, update the internal state
  useEffect(() => {
    if (initialTaskId && initialTaskId !== taskId) {
      setTaskId(initialTaskId);
      if (autoRefresh) {
        checkTaskStatus(initialTaskId);
      }
    }
  }, [initialTaskId, taskId, autoRefresh, checkTaskStatus]);

  // Handle manual task ID input
  const handleTaskIdSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (taskId) {
        checkTaskStatus(taskId);
        if (autoRefresh) {
          startPolling();
        }
      }
    },
    [taskId, checkTaskStatus, autoRefresh, startPolling]
  );

  // Get progress percentage based on status
  const getProgressPercentage = () => {
    switch (status) {
      case 'pending':
        return 25;
      case 'processing':
        return 65;
      case 'completed':
        return 100;
      case 'failed':
        return 100;
      default:
        return 0;
    }
  };

  // Format date for display
  const formatDate = (timestamp?: number) => {
    if (!timestamp) return 'N/A';
    return new Date(timestamp * 1000).toLocaleString();
  };

  // Handle fetching the result
  const handleFetchResult = useCallback(() => {
    if (taskId) {
      getTaskResult(taskId);
    }
  }, [taskId, getTaskResult]);

  return (
    <div className={className}>
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="p-4 border-b">
          <h2 className="text-lg font-medium text-gray-900">Async Task Manager</h2>
        </div>

        <div className="p-4">
          <form onSubmit={handleTaskIdSubmit} className="flex space-x-2 mb-4">
            <input
              type="text"
              value={taskId || ''}
              onChange={(e) => setTaskId(e.target.value)}
              placeholder="Enter task ID"
              className="flex-1 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            />
            <button
              type="submit"
              disabled={!taskId}
              className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-indigo-300"
            >
              Check Status
            </button>
          </form>

          {taskId && (
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-medium text-gray-700">Task Status</h3>
                <div className="mt-2 p-3 bg-gray-50 rounded-md">
                  <div className="flex justify-between items-center mb-2">
                    <span
                      className={`text-sm font-medium ${
                        status === 'completed'
                          ? 'text-green-700'
                          : status === 'failed'
                          ? 'text-red-700'
                          : 'text-blue-700'
                      }`}
                    >
                      {status || 'Unknown'}
                    </span>
                    <span className="text-xs text-gray-500">ID: {taskId}</span>
                  </div>

                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        status === 'completed'
                          ? 'bg-green-600'
                          : status === 'failed'
                          ? 'bg-red-600'
                          : 'bg-blue-600'
                      }`}
                      style={{ width: `${getProgressPercentage()}%` }}
                    ></div>
                  </div>
                </div>
              </div>

              <div className="flex space-x-2">
                {['pending', 'processing'].includes(status || '') && (
                  <>
                    {isPolling ? (
                      <button
                        onClick={stopPolling}
                        className="inline-flex items-center px-3 py-1 border border-transparent text-sm leading-4 font-medium rounded-md text-red-700 bg-red-100 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                      >
                        Stop Polling
                      </button>
                    ) : (
                      <button
                        onClick={startPolling}
                        className="inline-flex items-center px-3 py-1 border border-transparent text-sm leading-4 font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                      >
                        Start Polling
                      </button>
                    )}
                  </>
                )}

                {status === 'completed' && (
                  <button
                    onClick={handleFetchResult}
                    className="inline-flex items-center px-3 py-1 border border-transparent text-sm leading-4 font-medium rounded-md text-green-700 bg-green-100 hover:bg-green-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                  >
                    Fetch Result
                  </button>
                )}
              </div>

              {error && (
                <div className="p-3 bg-red-50 text-red-800 rounded-md">
                  <h3 className="text-sm font-medium">Error</h3>
                  <p className="text-sm">{error.message}</p>
                </div>
              )}

              {showResultPreview && response && (
                <div>
                  <h3 className="text-sm font-medium text-gray-700">Result Preview</h3>
                  <div className="mt-2 p-3 bg-gray-50 rounded-md overflow-auto max-h-60">
                    <pre className="text-xs whitespace-pre-wrap">
                      {typeof response === 'object'
                        ? JSON.stringify(response, null, 2)
                        : String(response)}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AsyncTaskManager;