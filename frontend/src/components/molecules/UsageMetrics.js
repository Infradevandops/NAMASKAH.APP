import React, { useState, useMemo } from 'react';
import PropTypes from 'prop-types';
import { Button, Icon } from '../atoms';

const UsageMetrics = ({
  currentPlan = 'pro',
  usageData = {},
  billingPeriod = { start: '', end: '' },
  onUpgradePlan,
  className = '',
  ...props
}) => {
  const [selectedMetric, setSelectedMetric] = useState('sms');
  const [timeRange, setTimeRange] = useState('current');

  // Plan limits
  const planLimits = {
    basic: {
      sms: 1000,
      numbers: 5,
      users: 3,
      apiCalls: 10000
    },
    pro: {
      sms: 10000,
      numbers: 25,
      users: 10,
      apiCalls: 100000
    },
    enterprise: {
      sms: -1, // unlimited
      numbers: -1,
      users: -1,
      apiCalls: -1
    }
  };

  // Current usage (mock data if not provided)
  const currentUsage = {
    sms: usageData.sms || 7250,
    numbers: usageData.numbers || 12,
    users: usageData.users || 6,
    apiCalls: usageData.apiCalls || 45000,
    ...usageData
  };

  // Historical data for charts (mock data)
  const historicalData = {
    sms: [
      { date: '2024-01-01', value: 850 },
      { date: '2024-01-02', value: 920 },
      { date: '2024-01-03', value: 1100 },
      { date: '2024-01-04', value: 980 },
      { date: '2024-01-05', value: 1250 },
      { date: '2024-01-06', value: 1180 },
      { date: '2024-01-07', value: 1350 }
    ],
    apiCalls: [
      { date: '2024-01-01', value: 4200 },
      { date: '2024-01-02', value: 4800 },
      { date: '2024-01-03', value: 5100 },
      { date: '2024-01-04', value: 4900 },
      { date: '2024-01-05', value: 5400 },
      { date: '2024-01-06', value: 5200 },
      { date: '2024-01-07', value: 5800 }
    ]
  };

  const getUsagePercentage = (used, limit) => {
    if (limit === -1) return 0; // unlimited
    return Math.min((used / limit) * 100, 100);
  };

  const getUsageColor = (percentage) => {
    if (percentage >= 90) return 'text-red-600 bg-red-100';
    if (percentage >= 75) return 'text-yellow-600 bg-yellow-100';
    return 'text-green-600 bg-green-100';
  };

  const getProgressBarColor = (percentage) => {
    if (percentage >= 90) return 'bg-red-500';
    if (percentage >= 75) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const formatNumber = (num) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    });
  };

  const calculateCost = (usage, unitCost) => {
    return (usage * unitCost).toFixed(2);
  };

  // Unit costs (example pricing)
  const unitCosts = {
    sms: 0.01, // $0.01 per SMS
    apiCalls: 0.0001, // $0.0001 per API call
    numbers: 2.00, // $2.00 per number per month
    users: 5.00 // $5.00 per user per month
  };

  const metrics = useMemo(() => [
    {
      key: 'sms',
      name: 'SMS Messages',
      icon: 'messageSquare',
      current: currentUsage.sms,
      limit: planLimits[currentPlan].sms,
      unit: 'messages',
      cost: calculateCost(currentUsage.sms, unitCosts.sms)
    },
    {
      key: 'numbers',
      name: 'Phone Numbers',
      icon: 'phone',
      current: currentUsage.numbers,
      limit: planLimits[currentPlan].numbers,
      unit: 'numbers',
      cost: calculateCost(currentUsage.numbers, unitCosts.numbers)
    },
    {
      key: 'users',
      name: 'Team Members',
      icon: 'users',
      current: currentUsage.users,
      limit: planLimits[currentPlan].users,
      unit: 'users',
      cost: calculateCost(currentUsage.users, unitCosts.users)
    },
    {
      key: 'apiCalls',
      name: 'API Calls',
      icon: 'code',
      current: currentUsage.apiCalls,
      limit: planLimits[currentPlan].apiCalls,
      unit: 'calls',
      cost: calculateCost(currentUsage.apiCalls, unitCosts.apiCalls)
    }
  ], [currentUsage, currentPlan]);

  const totalMonthlyCost = metrics.reduce((sum, metric) => sum + parseFloat(metric.cost), 0);

  return (
    <div className={`space-y-6 ${className}`} {...props}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Usage & Analytics</h3>
          <p className="text-sm text-gray-600">
            Monitor your usage and costs for the current billing period
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="text-sm border border-gray-300 rounded-md px-3 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="current">Current Period</option>
            <option value="last30">Last 30 Days</option>
            <option value="last90">Last 90 Days</option>
          </select>
          
          <Button variant="outline" size="sm">
            <Icon name="download" size="sm" className="mr-1" />
            Export
          </Button>
        </div>
      </div>

      {/* Billing Period Info */}
      {billingPeriod.start && billingPeriod.end && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-sm font-medium text-blue-900">Current Billing Period</h4>
              <p className="text-sm text-blue-700">
                {formatDate(billingPeriod.start)} - {formatDate(billingPeriod.end)}
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm font-medium text-blue-900">Estimated Cost</p>
              <p className="text-lg font-bold text-blue-900">${totalMonthlyCost.toFixed(2)}</p>
            </div>
          </div>
        </div>
      )}

      {/* Usage Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((metric) => {
          const percentage = getUsagePercentage(metric.current, metric.limit);
          const isUnlimited = metric.limit === -1;
          
          return (
            <div
              key={metric.key}
              className={`bg-white border rounded-lg p-4 cursor-pointer transition-colors ${
                selectedMetric === metric.key ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => setSelectedMetric(metric.key)}
            >
              <div className="flex items-center justify-between mb-3">
                <Icon name={metric.icon} size="md" className="text-gray-400" />
                <span className={`text-xs font-medium px-2 py-1 rounded-full ${getUsageColor(percentage)}`}>
                  {isUnlimited ? 'Unlimited' : `${percentage.toFixed(0)}%`}
                </span>
              </div>
              
              <div className="mb-2">
                <h4 className="text-sm font-medium text-gray-900">{metric.name}</h4>
                <p className="text-2xl font-bold text-gray-900">
                  {formatNumber(metric.current)}
                  {!isUnlimited && (
                    <span className="text-sm font-normal text-gray-500">
                      /{formatNumber(metric.limit)}
                    </span>
                  )}
                </p>
              </div>
              
              {!isUnlimited && (
                <div className="mb-2">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all ${getProgressBarColor(percentage)}`}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              )}
              
              <div className="flex items-center justify-between text-xs text-gray-500">
                <span>{metric.unit}</span>
                <span>${metric.cost}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Detailed Chart View */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-lg font-semibold text-gray-900">
            {metrics.find(m => m.key === selectedMetric)?.name} Usage Trend
          </h4>
          
          <div className="flex items-center space-x-2">
            <Button
              variant={selectedMetric === 'sms' ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => setSelectedMetric('sms')}
            >
              SMS
            </Button>
            <Button
              variant={selectedMetric === 'apiCalls' ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => setSelectedMetric('apiCalls')}
            >
              API Calls
            </Button>
          </div>
        </div>

        {/* Simple Chart (would use a real chart library in production) */}
        <div className="h-64 flex items-end space-x-2 border-b border-gray-200 pb-4">
          {(historicalData[selectedMetric] || []).map((dataPoint, index) => {
            const maxValue = Math.max(...(historicalData[selectedMetric] || []).map(d => d.value));
            const height = (dataPoint.value / maxValue) * 100;
            
            return (
              <div key={index} className="flex-1 flex flex-col items-center">
                <div
                  className="w-full bg-blue-500 rounded-t transition-all hover:bg-blue-600"
                  style={{ height: `${height}%` }}
                  title={`${formatDate(dataPoint.date)}: ${formatNumber(dataPoint.value)}`}
                />
                <span className="text-xs text-gray-500 mt-2">
                  {formatDate(dataPoint.date)}
                </span>
              </div>
            );
          })}
        </div>

        <div className="mt-4 grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-sm text-gray-600">Average Daily</p>
            <p className="text-lg font-semibold text-gray-900">
              {formatNumber(
                (historicalData[selectedMetric] || []).reduce((sum, d) => sum + d.value, 0) / 
                (historicalData[selectedMetric] || []).length || 0
              )}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Peak Day</p>
            <p className="text-lg font-semibold text-gray-900">
              {formatNumber(Math.max(...(historicalData[selectedMetric] || []).map(d => d.value)))}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Total This Week</p>
            <p className="text-lg font-semibold text-gray-900">
              {formatNumber((historicalData[selectedMetric] || []).reduce((sum, d) => sum + d.value, 0))}
            </p>
          </div>
        </div>
      </div>

      {/* Usage Alerts */}
      <div className="space-y-3">
        {metrics.map((metric) => {
          const percentage = getUsagePercentage(metric.current, metric.limit);
          if (percentage < 75 || metric.limit === -1) return null;
          
          return (
            <div
              key={metric.key}
              className={`border rounded-lg p-4 ${
                percentage >= 90 ? 'bg-red-50 border-red-200' : 'bg-yellow-50 border-yellow-200'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start">
                  <Icon 
                    name={percentage >= 90 ? 'alertCircle' : 'alertTriangle'} 
                    size="sm" 
                    className={`mt-0.5 mr-3 ${
                      percentage >= 90 ? 'text-red-600' : 'text-yellow-600'
                    }`} 
                  />
                  <div>
                    <h4 className={`text-sm font-medium ${
                      percentage >= 90 ? 'text-red-900' : 'text-yellow-900'
                    }`}>
                      {percentage >= 90 ? 'Usage Limit Nearly Reached' : 'High Usage Alert'}
                    </h4>
                    <p className={`text-sm ${
                      percentage >= 90 ? 'text-red-700' : 'text-yellow-700'
                    }`}>
                      You've used {percentage.toFixed(0)}% of your {metric.name.toLowerCase()} limit 
                      ({formatNumber(metric.current)} of {formatNumber(metric.limit)})
                    </p>
                  </div>
                </div>
                
                {percentage >= 90 && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={onUpgradePlan}
                    className="border-red-300 text-red-700 hover:bg-red-100"
                  >
                    Upgrade Plan
                  </Button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Cost Breakdown */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h4 className="text-lg font-semibold text-gray-900 mb-4">Cost Breakdown</h4>
        
        <div className="space-y-3">
          {metrics.map((metric) => (
            <div key={metric.key} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-b-0">
              <div className="flex items-center">
                <Icon name={metric.icon} size="sm" className="text-gray-400 mr-3" />
                <div>
                  <span className="text-sm font-medium text-gray-900">{metric.name}</span>
                  <span className="text-sm text-gray-500 ml-2">
                    {formatNumber(metric.current)} {metric.unit}
                  </span>
                </div>
              </div>
              <span className="text-sm font-medium text-gray-900">${metric.cost}</span>
            </div>
          ))}
          
          <div className="flex items-center justify-between py-2 pt-4 border-t border-gray-200">
            <span className="text-base font-semibold text-gray-900">Total Estimated Cost</span>
            <span className="text-lg font-bold text-gray-900">${totalMonthlyCost.toFixed(2)}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

UsageMetrics.propTypes = {
  currentPlan: PropTypes.oneOf(['basic', 'pro', 'enterprise']),
  usageData: PropTypes.shape({
    sms: PropTypes.number,
    numbers: PropTypes.number,
    users: PropTypes.number,
    apiCalls: PropTypes.number
  }),
  billingPeriod: PropTypes.shape({
    start: PropTypes.string,
    end: PropTypes.string
  }),
  onUpgradePlan: PropTypes.func,
  className: PropTypes.string
};

export default UsageMetrics;