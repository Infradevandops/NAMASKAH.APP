import React, { useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import { Button, Icon } from '../atoms';
import { InteractiveChart } from '../molecules';

const AnalyticsDashboard = ({
  dashboardType = 'overview',
  timeRange = '7d',
  onTimeRangeChange,
  onExportDashboard,
  className = '',
  ...props
}) => {
  const [widgets, setWidgets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedWidget, setSelectedWidget] = useState(null);
  const [dashboardLayout, setDashboardLayout] = useState('grid');
  const [refreshInterval, setRefreshInterval] = useState(null);

  // Mock data for different dashboard types
  const mockData = {
    overview: {
      totalMessages: { current: 15420, previous: 14230, trend: 8.4 },
      successRate: { current: 94.2, previous: 92.1, trend: 2.3 },
      avgResponseTime: { current: 245, previous: 280, trend: -12.5 },
      activeCampaigns: { current: 12, previous: 10, trend: 20 },
      revenue: { current: 2840, previous: 2650, trend: 7.2 },
      costs: { current: 1420, previous: 1380, trend: 2.9 }
    },
    messaging: {
      messagesPerHour: [
        { date: '2024-01-01T00:00:00Z', value: 120 },
        { date: '2024-01-01T01:00:00Z', value: 95 },
        { date: '2024-01-01T02:00:00Z', value: 80 },
        { date: '2024-01-01T03:00:00Z', value: 65 },
        { date: '2024-01-01T04:00:00Z', value: 45 },
        { date: '2024-01-01T05:00:00Z', value: 70 },
        { date: '2024-01-01T06:00:00Z', value: 110 }
      ],
      deliveryStatus: [
        { label: 'Delivered', value: 8420, color: '#10b981' },
        { label: 'Pending', value: 340, color: '#f59e0b' },
        { label: 'Failed', value: 180, color: '#ef4444' }
      ]
    },
    performance: {
      responseTime: [
        { date: '2024-01-01', value: 250 },
        { date: '2024-01-02', value: 230 },
        { date: '2024-01-03', value: 240 },
        { date: '2024-01-04', value: 220 },
        { date: '2024-01-05', value: 210 },
        { date: '2024-01-06', value: 225 },
        { date: '2024-01-07', value: 200 }
      ],
      errorRates: [
        { date: '2024-01-01', value: 2.1 },
        { date: '2024-01-02', value: 1.8 },
        { date: '2024-01-03', value: 2.3 },
        { date: '2024-01-04', value: 1.5 },
        { date: '2024-01-05', value: 1.2 },
        { date: '2024-01-06', value: 1.7 },
        { date: '2024-01-07', value: 1.4 }
      ]
    }
  };

  const fetchDashboardData = useCallback(async () => {
    setLoading(true);

    // Simulate API call
    setTimeout(() => {
      const dashboardWidgets = [
        {
          id: 'messages-sent',
          title: 'Messages Sent',
          type: 'metric',
          value: mockData[dashboardType].totalMessages?.current || mockData.overview.totalMessages.current,
          previousValue: mockData[dashboardType].totalMessages?.previous || mockData.overview.totalMessages.previous,
          trend: mockData[dashboardType].totalMessages?.trend || mockData.overview.totalMessages.trend,
          icon: 'messageSquare',
          color: 'blue'
        },
        {
          id: 'success-rate',
          title: 'Success Rate',
          type: 'metric',
          value: mockData[dashboardType].successRate?.current || mockData.overview.successRate.current,
          previousValue: mockData[dashboardType].successRate?.previous || mockData.overview.successRate.previous,
          trend: mockData[dashboardType].successRate?.trend || mockData.overview.successRate.trend,
          icon: 'target',
          color: 'green',
          unit: '%'
        },
        {
          id: 'response-time',
          title: 'Avg Response Time',
          type: 'metric',
          value: mockData[dashboardType].avgResponseTime?.current || mockData.overview.avgResponseTime.current,
          previousValue: mockData[dashboardType].avgResponseTime?.previous || mockData.overview.avgResponseTime.previous,
          trend: mockData[dashboardType].avgResponseTime?.trend || mockData.overview.avgResponseTime.trend,
          icon: 'clock',
          color: 'purple',
          unit: 'ms'
        },
        {
          id: 'revenue',
          title: 'Revenue',
          type: 'metric',
          value: mockData[dashboardType].revenue?.current || mockData.overview.revenue.current,
          previousValue: mockData[dashboardType].revenue?.previous || mockData.overview.revenue.previous,
          trend: mockData[dashboardType].revenue?.trend || mockData.overview.revenue.trend,
          icon: 'dollarSign',
          color: 'green',
          unit: '$'
        },
        {
          id: 'messages-chart',
          title: 'Message Volume',
          type: 'chart',
          chartType: 'line',
          data: mockData.messaging.messagesPerHour,
          size: 'large'
        },
        {
          id: 'delivery-status',
          title: 'Delivery Status',
          type: 'chart',
          chartType: 'pie',
          data: mockData.messaging.deliveryStatus,
          size: 'medium'
        },
        {
          id: 'performance-trend',
          title: 'Performance Trend',
          type: 'chart',
          chartType: 'area',
          data: mockData.performance.responseTime,
          size: 'large'
        },
        {
          id: 'error-rates',
          title: 'Error Rates',
          type: 'chart',
          chartType: 'bar',
          data: mockData.performance.errorRates,
          size: 'medium'
        }
      ];

      setWidgets(dashboardWidgets);
      setLoading(false);
    }, 1000);
  }, [dashboardType]);

  useEffect(() => {
    fetchDashboardData();

    // Set up auto-refresh
    if (refreshInterval) {
      const interval = setInterval(fetchDashboardData, refreshInterval * 1000);
      return () => clearInterval(interval);
    }
  }, [dashboardType, timeRange, refreshInterval, fetchDashboardData]);

  const formatMetricValue = (value, unit = '') => {
    if (unit === '$') {
      return `$${value.toLocaleString()}`;
    }
    if (unit === '%') {
      return `${value.toFixed(1)}%`;
    }
    if (unit === 'ms') {
      return `${value}ms`;
    }
    return value.toLocaleString();
  };

  const getTrendColor = (trend) => {
    if (trend > 0) return 'text-green-600';
    if (trend < 0) return 'text-red-600';
    return 'text-gray-500';
  };

  const getTrendIcon = (trend) => {
    if (trend > 0) return 'trendingUp';
    if (trend < 0) return 'trendingDown';
    return 'minus';
  };

  const getWidgetGridClass = (size) => {
    switch (size) {
      case 'small': return 'col-span-1';
      case 'medium': return 'col-span-1 md:col-span-2';
      case 'large': return 'col-span-1 md:col-span-2 lg:col-span-3';
      case 'full': return 'col-span-full';
      default: return 'col-span-1';
    }
  };

  const handleWidgetClick = (widget) => {
    setSelectedWidget(widget);
  };

  const handleRefreshData = () => {
    fetchDashboardData();
  };

  const handleAutoRefreshToggle = (interval) => {
    setRefreshInterval(interval === refreshInterval ? null : interval);
  };

  if (loading) {
    return (
      <div className={`bg-white border border-gray-200 rounded-lg p-6 ${className}`}>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-500">Loading dashboard...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`} {...props}>
      {/* Dashboard Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h2>
          <p className="text-gray-600">Real-time insights and performance metrics</p>
        </div>
        
        <div className="flex items-center space-x-2">
          {/* Auto-refresh controls */}
          <div className="flex items-center space-x-1 border border-gray-300 rounded-md">
            <Button
              variant={refreshInterval === 30 ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => handleAutoRefreshToggle(30)}
              className="rounded-r-none border-r border-gray-300"
            >
              30s
            </Button>
            <Button
              variant={refreshInterval === 60 ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => handleAutoRefreshToggle(60)}
              className="rounded-none border-r border-gray-300"
            >
              1m
            </Button>
            <Button
              variant={refreshInterval === 300 ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => handleAutoRefreshToggle(300)}
              className="rounded-l-none"
            >
              5m
            </Button>
          </div>
          
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefreshData}
          >
            <Icon name="refresh" size="sm" className="mr-1" />
            Refresh
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => setDashboardLayout(dashboardLayout === 'grid' ? 'list' : 'grid')}
          >
            <Icon name={dashboardLayout === 'grid' ? 'list' : 'grid'} size="sm" />
          </Button>
          
          {onExportDashboard && (
            <Button
              variant="outline"
              size="sm"
              onClick={onExportDashboard}
            >
              <Icon name="download" size="sm" className="mr-1" />
              Export
            </Button>
          )}
        </div>
      </div>

      {/* Auto-refresh indicator */}
      {refreshInterval && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse"></div>
            <span className="text-sm text-blue-800">
              Auto-refreshing every {refreshInterval < 60 ? `${refreshInterval}s` : `${refreshInterval / 60}m`}
            </span>
            <Button
              variant="ghost"
              size="xs"
              onClick={() => setRefreshInterval(null)}
              className="text-blue-600 hover:text-blue-800"
            >
              <Icon name="x" size="xs" />
            </Button>
          </div>
        </div>
      )}

      {/* Dashboard Widgets */}
      <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 ${dashboardLayout === 'list' ? 'lg:grid-cols-1' : ''}`}>
        {widgets.map((widget) => (
          <div
            key={widget.id}
            className={`${getWidgetGridClass(widget.size)} ${
              dashboardLayout === 'list' ? 'col-span-full' : ''
            }`}
          >
            {widget.type === 'metric' ? (
              <div 
                className="bg-white border border-gray-200 rounded-lg p-6 cursor-pointer hover:border-gray-300 transition-colors"
                onClick={() => handleWidgetClick(widget)}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">{widget.title}</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {formatMetricValue(widget.value, widget.unit)}
                    </p>
                    
                    {widget.trend !== undefined && (
                      <div className={`flex items-center space-x-1 mt-1 ${getTrendColor(widget.trend)}`}>
                        <Icon name={getTrendIcon(widget.trend)} size="sm" />
                        <span className="text-sm font-medium">
                          {Math.abs(widget.trend).toFixed(1)}%
                        </span>
                        <span className="text-xs text-gray-500">vs last period</span>
                      </div>
                    )}
                  </div>
                  
                  <Icon name={widget.icon} size="lg" className={`text-${widget.color}-500`} />
                </div>
              </div>
            ) : (
              <InteractiveChart
                type={widget.chartType}
                data={widget.data}
                title={widget.title}
                height={dashboardLayout === 'list' ? 200 : 300}
                showControls={false}
                onDataPointClick={(data, index) => console.log('Data point clicked:', data, index)}
              />
            )}
          </div>
        ))}
      </div>

      {/* Widget Detail Modal */}
      {selectedWidget && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{selectedWidget.title}</h3>
                <p className="text-sm text-gray-600">Detailed view and analysis</p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedWidget(null)}
              >
                <Icon name="x" size="sm" />
              </Button>
            </div>
            
            <div className="p-6">
              {selectedWidget.type === 'metric' ? (
                <div className="space-y-6">
                  {/* Metric Details */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="text-center p-4 bg-gray-50 rounded-lg">
                      <div className="text-3xl font-bold text-gray-900 mb-2">
                        {formatMetricValue(selectedWidget.value, selectedWidget.unit)}
                      </div>
                      <div className="text-sm text-gray-600">Current Value</div>
                    </div>
                    
                    <div className="text-center p-4 bg-gray-50 rounded-lg">
                      <div className="text-3xl font-bold text-gray-900 mb-2">
                        {formatMetricValue(selectedWidget.previousValue, selectedWidget.unit)}
                      </div>
                      <div className="text-sm text-gray-600">Previous Period</div>
                    </div>
                    
                    <div className="text-center p-4 bg-gray-50 rounded-lg">
                      <div className={`text-3xl font-bold mb-2 ${getTrendColor(selectedWidget.trend)}`}>
                        {selectedWidget.trend > 0 ? '+' : ''}{selectedWidget.trend.toFixed(1)}%
                      </div>
                      <div className="text-sm text-gray-600">Change</div>
                    </div>
                  </div>
                  
                  {/* Historical Chart */}
                  <InteractiveChart
                    type="line"
                    data={mockData.messaging.messagesPerHour}
                    title={`${selectedWidget.title} Trend`}
                    height={300}
                  />
                </div>
              ) : (
                <InteractiveChart
                  type={selectedWidget.chartType}
                  data={selectedWidget.data}
                  title={selectedWidget.title}
                  height={400}
                  showControls={true}
                />
              )}
            </div>
          </div>
        </div>
      )}

      {/* Dashboard Controls */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Icon name="clock" size="sm" className="text-gray-400" />
              <span className="text-sm text-gray-600">Last updated:</span>
              <span className="text-sm font-medium text-gray-900">
                {new Date().toLocaleTimeString()}
              </span>
            </div>
            
            {refreshInterval && (
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-sm text-green-600">Live updates enabled</span>
              </div>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => console.log('Customize dashboard')}
            >
              <Icon name="settings" size="sm" className="mr-1" />
              Customize
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => console.log('Share dashboard')}
            >
              <Icon name="share" size="sm" className="mr-1" />
              Share
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

AnalyticsDashboard.propTypes = {
  dashboardType: PropTypes.oneOf(['overview', 'messaging', 'performance', 'financial']),
  timeRange: PropTypes.string,
  onTimeRangeChange: PropTypes.func,
  onExportDashboard: PropTypes.func,
  className: PropTypes.string
};

export default AnalyticsDashboard;