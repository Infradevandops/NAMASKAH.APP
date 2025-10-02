import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { Button, Icon } from '../atoms';

const SubscriptionPlans = ({
  currentPlan = 'basic',
  onPlanChange,
  onUpgrade,
  onDowngrade,
  className = '',
  ...props
}) => {
  const [selectedPlan, setSelectedPlan] = useState(currentPlan);
  const [billingCycle, setBillingCycle] = useState('monthly');

  const plans = {
    basic: {
      name: 'Basic',
      description: 'Perfect for individuals and small teams',
      monthlyPrice: 9.99,
      yearlyPrice: 99.99,
      features: [
        '1,000 SMS messages/month',
        '5 phone numbers',
        'Basic analytics',
        'Email support',
        'Standard API access'
      ],
      limits: {
        sms: '1,000/month',
        numbers: '5',
        users: '3'
      },
      popular: false
    },
    pro: {
      name: 'Professional',
      description: 'Ideal for growing businesses',
      monthlyPrice: 29.99,
      yearlyPrice: 299.99,
      features: [
        '10,000 SMS messages/month',
        '25 phone numbers',
        'Advanced analytics',
        'Priority support',
        'Full API access',
        'Custom integrations',
        'Team collaboration'
      ],
      limits: {
        sms: '10,000/month',
        numbers: '25',
        users: '10'
      },
      popular: true
    },
    enterprise: {
      name: 'Enterprise',
      description: 'For large organizations with custom needs',
      monthlyPrice: 99.99,
      yearlyPrice: 999.99,
      features: [
        'Unlimited SMS messages',
        'Unlimited phone numbers',
        'Real-time analytics',
        '24/7 dedicated support',
        'Custom API endpoints',
        'White-label options',
        'Advanced security',
        'SLA guarantees'
      ],
      limits: {
        sms: 'Unlimited',
        numbers: 'Unlimited',
        users: 'Unlimited'
      },
      popular: false
    }
  };

  const getPrice = (plan) => {
    return billingCycle === 'monthly' ? plan.monthlyPrice : plan.yearlyPrice;
  };

  const getSavings = (plan) => {
    const monthlyTotal = plan.monthlyPrice * 12;
    const yearlyPrice = plan.yearlyPrice;
    return monthlyTotal - yearlyPrice;
  };

  const handlePlanSelect = (planKey) => {
    setSelectedPlan(planKey);
    onPlanChange?.(planKey, billingCycle);
  };

  const handleUpgrade = (planKey) => {
    onUpgrade?.(planKey, billingCycle);
  };

  const handleDowngrade = (planKey) => {
    onDowngrade?.(planKey, billingCycle);
  };

  const isPlanUpgrade = (planKey) => {
    const planOrder = { basic: 1, pro: 2, enterprise: 3 };
    return planOrder[planKey] > planOrder[currentPlan];
  };

  const isPlanDowngrade = (planKey) => {
    const planOrder = { basic: 1, pro: 2, enterprise: 3 };
    return planOrder[planKey] < planOrder[currentPlan];
  };

  return (
    <div className={`space-y-6 ${className}`} {...props}>
      {/* Billing Cycle Toggle */}
      <div className="flex items-center justify-center">
        <div className="bg-gray-100 p-1 rounded-lg flex">
          <button
            onClick={() => setBillingCycle('monthly')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              billingCycle === 'monthly'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Monthly
          </button>
          <button
            onClick={() => setBillingCycle('yearly')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              billingCycle === 'yearly'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Yearly
            <span className="ml-1 text-xs text-green-600 font-semibold">Save 17%</span>
          </button>
        </div>
      </div>

      {/* Plans Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {Object.entries(plans).map(([planKey, plan]) => (
          <div
            key={planKey}
            className={`relative bg-white border rounded-lg shadow-sm hover:shadow-md transition-shadow ${
              plan.popular ? 'border-blue-500 ring-2 ring-blue-500 ring-opacity-20' : 'border-gray-200'
            } ${
              selectedPlan === planKey ? 'bg-blue-50 border-blue-300' : ''
            }`}
          >
            {/* Popular Badge */}
            {plan.popular && (
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                <span className="bg-blue-500 text-white px-3 py-1 rounded-full text-xs font-medium">
                  Most Popular
                </span>
              </div>
            )}

            {/* Current Plan Badge */}
            {currentPlan === planKey && (
              <div className="absolute -top-3 right-4">
                <span className="bg-green-500 text-white px-3 py-1 rounded-full text-xs font-medium">
                  Current Plan
                </span>
              </div>
            )}

            <div className="p-6">
              {/* Plan Header */}
              <div className="text-center mb-6">
                <h3 className="text-xl font-semibold text-gray-900 mb-2">{plan.name}</h3>
                <p className="text-gray-600 text-sm mb-4">{plan.description}</p>
                
                <div className="mb-4">
                  <span className="text-4xl font-bold text-gray-900">
                    ${getPrice(plan).toFixed(2)}
                  </span>
                  <span className="text-gray-600 ml-1">
                    /{billingCycle === 'monthly' ? 'month' : 'year'}
                  </span>
                </div>

                {billingCycle === 'yearly' && (
                  <p className="text-sm text-green-600 font-medium">
                    Save ${getSavings(plan).toFixed(2)} per year
                  </p>
                )}
              </div>

              {/* Features List */}
              <ul className="space-y-3 mb-6">
                {plan.features.map((feature, index) => (
                  <li key={index} className="flex items-start">
                    <Icon name="check" size="sm" className="text-green-500 mt-0.5 mr-3 flex-shrink-0" />
                    <span className="text-sm text-gray-700">{feature}</span>
                  </li>
                ))}
              </ul>

              {/* Usage Limits */}
              <div className="bg-gray-50 rounded-lg p-4 mb-6">
                <h4 className="text-sm font-medium text-gray-900 mb-3">Usage Limits</h4>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">SMS Messages:</span>
                    <span className="font-medium">{plan.limits.sms}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Phone Numbers:</span>
                    <span className="font-medium">{plan.limits.numbers}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Team Members:</span>
                    <span className="font-medium">{plan.limits.users}</span>
                  </div>
                </div>
              </div>

              {/* Action Button */}
              <div className="space-y-2">
                {currentPlan === planKey ? (
                  <Button
                    variant="outline"
                    className="w-full"
                    disabled
                  >
                    <Icon name="check" size="sm" className="mr-2" />
                    Current Plan
                  </Button>
                ) : isPlanUpgrade(planKey) ? (
                  <Button
                    variant="primary"
                    className="w-full"
                    onClick={() => handleUpgrade(planKey)}
                  >
                    <Icon name="arrowUp" size="sm" className="mr-2" />
                    Upgrade to {plan.name}
                  </Button>
                ) : isPlanDowngrade(planKey) ? (
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => handleDowngrade(planKey)}
                  >
                    <Icon name="arrowDown" size="sm" className="mr-2" />
                    Downgrade to {plan.name}
                  </Button>
                ) : (
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => handlePlanSelect(planKey)}
                  >
                    Select {plan.name}
                  </Button>
                )}

                {planKey !== 'basic' && (
                  <p className="text-xs text-gray-500 text-center">
                    14-day free trial • Cancel anytime
                  </p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Plan Comparison */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Need help choosing?</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h4 className="font-medium text-gray-900 mb-2">Choose Basic if:</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• You're just getting started</li>
              <li>• You send less than 1,000 SMS per month</li>
              <li>• You have a small team (1-3 people)</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-gray-900 mb-2">Choose Pro if:</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• You're a growing business</li>
              <li>• You need advanced analytics</li>
              <li>• You want priority support</li>
            </ul>
          </div>
        </div>
        
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-sm text-gray-600">
            <strong>Enterprise customers:</strong> Contact our sales team for custom pricing and features.
          </p>
          <Button variant="outline" size="sm" className="mt-2">
            Contact Sales
          </Button>
        </div>
      </div>
    </div>
  );
};

SubscriptionPlans.propTypes = {
  currentPlan: PropTypes.oneOf(['basic', 'pro', 'enterprise']),
  onPlanChange: PropTypes.func,
  onUpgrade: PropTypes.func,
  onDowngrade: PropTypes.func,
  className: PropTypes.string
};

export default SubscriptionPlans;