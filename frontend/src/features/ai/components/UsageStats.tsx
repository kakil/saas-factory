import React, { useState, useEffect, useCallback } from 'react';
import { useAIUsageStats } from '../hooks';

interface UsageStatsProps {
  defaultTimeframe?: 'day' | 'week' | 'month';
  autoRefresh?: boolean;
  refreshInterval?: number; // in milliseconds
  className?: string;
}

export const UsageStats: React.FC<UsageStatsProps> = ({
  defaultTimeframe = 'day',
  autoRefresh = false,
  refreshInterval = 30000, // 30 seconds
  className,
}) => {
  const [timeframe, setTimeframe] = useState<'day' | 'week' | 'month'>(defaultTimeframe);
  const { getUsageStats, isLoading, error, stats, reset } = useAIUsageStats();

  const fetchStats = useCallback(() => {
    getUsageStats(timeframe);
  }, [getUsageStats, timeframe]);

  // Fetch stats on mount and when timeframe changes
  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  // Set up auto-refresh if enabled
  useEffect(() => {
    if (!autoRefresh) return;
    
    const intervalId = setInterval(() => {
      fetchStats();
    }, refreshInterval);
    
    return () => clearInterval(intervalId);
  }, [autoRefresh, refreshInterval, fetchStats]);

  // Format date for display
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  // Create chart data for daily breakdown
  const dailyData = stats?.user?.stats.daily_breakdown || {};
  const dailyLabels = Object.keys(dailyData).sort();
  const dailyRequests = dailyLabels.map(date => dailyData[date]?.requests || 0);
  const dailyTokens = dailyLabels.map(date => dailyData[date]?.tokens || 0);

  return (
    <div className={className}>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-medium text-gray-900">AI Usage Statistics</h2>
        
        <div className="flex space-x-2">
          <select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value as 'day' | 'week' | 'month')}
            className="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
            disabled={isLoading}
          >
            <option value="day">Today</option>
            <option value="week">This Week</option>
            <option value="month">This Month</option>
          </select>
          
          <button
            onClick={fetchStats}
            disabled={isLoading}
            className="inline-flex items-center px-3 py-1 border border-transparent text-sm leading-4 font-medium rounded-md text-indigo-700 bg-indigo-100 hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            {isLoading ? 'Loading...' : 'Refresh'}
          </button>
        </div>
      </div>
      
      {error && (
        <div className="mb-4 p-3 bg-red-50 text-red-800 rounded-md">
          <p className="text-sm">{error.message}</p>
        </div>
      )}
      
      {isLoading && !stats && (
        <div className="flex justify-center items-center h-40">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
        </div>
      )}
      
      {stats && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="text-md font-medium text-gray-700 mb-2">Summary</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-gray-50 p-3 rounded-md">
                <span className="block text-sm text-gray-500">Period</span>
                <span className="block text-lg font-medium">
                  {formatDate(stats.period_start)} - {formatDate(stats.period_end)}
                </span>
              </div>
              
              <div className="bg-gray-50 p-3 rounded-md">
                <span className="block text-sm text-gray-500">Total Requests</span>
                <span className="block text-lg font-medium">
                  {stats.user?.stats.total_requests || 0}
                </span>
              </div>
              
              <div className="bg-gray-50 p-3 rounded-md">
                <span className="block text-sm text-gray-500">Total Tokens</span>
                <span className="block text-lg font-medium">
                  {stats.user?.stats.total_tokens || 0}
                </span>
              </div>
              
              <div className="bg-gray-50 p-3 rounded-md">
                <span className="block text-sm text-gray-500">Average Tokens per Request</span>
                <span className="block text-lg font-medium">
                  {stats.user?.stats.total_requests 
                    ? Math.round(stats.user.stats.total_tokens / stats.user.stats.total_requests) 
                    : 0}
                </span>
              </div>
            </div>
          </div>
          
          {dailyLabels.length > 0 && (
            <div className="bg-white rounded-lg shadow p-4">
              <h3 className="text-md font-medium text-gray-700 mb-2">Daily Breakdown</h3>
              
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Date
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Requests
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Tokens
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Avg. Tokens/Request
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {dailyLabels.map((date, index) => (
                      <tr key={date}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatDate(date)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {dailyRequests[index]}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {dailyTokens[index]}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {dailyRequests[index] 
                            ? Math.round(dailyTokens[index] / dailyRequests[index]) 
                            : 0}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
          
          {stats.tenant && (
            <div className="bg-white rounded-lg shadow p-4">
              <h3 className="text-md font-medium text-gray-700 mb-2">Organization Usage</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-gray-50 p-3 rounded-md">
                  <span className="block text-sm text-gray-500">Organization ID</span>
                  <span className="block text-lg font-medium">
                    {stats.tenant.id}
                  </span>
                </div>
                
                <div className="bg-gray-50 p-3 rounded-md">
                  <span className="block text-sm text-gray-500">Organization Requests</span>
                  <span className="block text-lg font-medium">
                    {stats.tenant.stats.total_requests}
                  </span>
                </div>
                
                <div className="bg-gray-50 p-3 rounded-md">
                  <span className="block text-sm text-gray-500">Organization Tokens</span>
                  <span className="block text-lg font-medium">
                    {stats.tenant.stats.total_tokens}
                  </span>
                </div>
                
                <div className="bg-gray-50 p-3 rounded-md">
                  <span className="block text-sm text-gray-500">User % of Org Usage</span>
                  <span className="block text-lg font-medium">
                    {stats.tenant.stats.total_tokens 
                      ? Math.round((stats.user?.stats.total_tokens || 0) / stats.tenant.stats.total_tokens * 100) 
                      : 0}%
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default UsageStats;