import React, { useState, useEffect } from 'react';
import axios from 'axios';
import LoadingSpinner from '../atoms/LoadingSpinner';
import { Icon } from '../atoms';

const VerificationAnalytics = () => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeRange, setTimeRange] = useState('7d'); // 7d, 30d, 90d

  // Fetch analytics data
  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`/api/verification/analytics?range=${timeRange}`);
      setAnalytics(response.data);
    } catch (err) {
      setError(err.message || 'Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [timeRange]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-600 text-center mt-4">
        Error: {error}
      </div>
    );
  }

  const { success_rate, total_verifications, average_completion_time, service_breakdown } = analytics || {};

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Verification Analytics</h1>

        {/* Time Range Selector */}
        <div className="flex space-x-2">
          {[
            { value: '7d', label: '7 Days' },
            { value: '30d', label: '30 Days' },
            { value: '90d', label: '90 Days' }
          ].map(({ value, label }) => (
            <button
              key={value}
              onClick={() => setTimeRange(value)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                timeRange === value
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <div className="flex items-center">
            <Icon name="check-circle" size="lg" className="text-green-500 mr-3" />
            <div>
              <p className="text-sm text-gray-600">Success Rate</p>
              <p className="text-2xl font-bold text-green-600">
                {success_rate ? `${(success_rate * 100).toFixed(1)}%` : 'N/A'}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md">
          <div className="flex items-center">
            <Icon name="activity" size="lg" className="text-blue-500 mr-3" />
            <div>
              <p className="text-sm text-gray-600">Total Verifications</p>
              <p className="text-2xl font-bold text-blue-600">
                {total_verifications || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md">
          <div className="flex items-center">
            <Icon name="clock" size="lg" className="text-orange-500 mr-3" />
            <div>
              <p className="text-sm text-gray-600">Avg Completion Time</p>
              <p className="text-2xl font-bold text-orange-600">
                {average_completion_time ? `${Math.round(average_completion_time)}s` : 'N/A'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Service Breakdown Chart */}
      <div className="bg-white p-6 rounded-lg shadow-md mb-8">
        <h2 className="text-xl font-semibold mb-4">Service Performance</h2>
        {service_breakdown && service_breakdown.length > 0 ? (
          <div className="space-y-4">
            {service_breakdown.map((service, index) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-4 h-4 rounded-full" style={{ backgroundColor: getServiceColor(service.service) }} />
                  <span className="font-medium">{service.service}</span>
                  <span className="text-sm text-gray-500">({service.count} verifications)</span>
                </div>
                <div className="flex items-center space-x-4">
                  <span className="text-sm text-gray-600">
                    Success: {(service.success_rate * 100).toFixed(1)}%
                  </span>
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div
                      className="h-2 rounded-full"
                      style={{
                        width: `${service.success_rate * 100}%`,
                        backgroundColor: getServiceColor(service.service)
                      }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-center py-8">No service data available</p>
        )}
      </div>

      {/* Recent Activity */}
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2 px-4">Service</th>
                <th className="text-left py-2 px-4">Status</th>
                <th className="text-left py-2 px-4">Duration</th>
                <th className="text-left py-2 px-4">Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {analytics?.recent_activity?.map((activity, index) => (
                <tr key={index} className="border-b hover:bg-gray-50">
                  <td className="py-2 px-4">{activity.service}</td>
                  <td className="py-2 px-4">
                    <span
                      className={`inline-block px-2 py-1 text-xs font-semibold rounded-full ${
                        activity.status === 'completed'
                          ? 'text-green-800 bg-green-200'
                          : activity.status === 'failed'
                          ? 'text-red-800 bg-red-200'
                          : 'text-yellow-800 bg-yellow-200'
                      }`}
                    >
                      {activity.status}
                    </span>
                  </td>
                  <td className="py-2 px-4">
                    {activity.duration ? `${Math.round(activity.duration)}s` : 'N/A'}
                  </td>
                  <td className="py-2 px-4 text-sm text-gray-500">
                    {new Date(activity.timestamp).toLocaleString()}
                  </td>
                </tr>
              )) || (
                <tr>
                  <td colSpan="4" className="py-8 text-center text-gray-500">
                    No recent activity
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// Helper function to get consistent colors for services
const getServiceColor = (service) => {
  const colors = {
    'textverified': '#3b82f6',
    'twilio': '#10b981',
    'default': '#6b7280'
  };
  return colors[service.toLowerCase()] || colors.default;
};

export default VerificationAnalytics;
