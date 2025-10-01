import React, { useState, useEffect } from 'react';
import { Header } from '../organisms';
import { 
  SubscriptionPlans, 
  PaymentMethods, 
  InvoiceHistory, 
  UsageMetrics,
  DataExporter,
  BillingForecastWidget
} from '../molecules';
import { Button, Icon } from '../atoms';

const BillingPage = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [planChangePreview, setPlanChangePreview] = useState(null);
  const [currentPlan, setCurrentPlan] = useState(null);
  const [billingCycle, setBillingCycle] = useState('monthly');
  const [usageData, setUsageData] = useState({});
  const [invoices, setInvoices] = useState([]);
  const [paymentMethods, setPaymentMethods] = useState([]);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [billingAlerts, setBillingAlerts] = useState([]);

  const tabs = [
    { id: 'overview', label: 'Overview', icon: 'creditCard' },
    { id: 'plans', label: 'Plans & Billing', icon: 'package' },
    { id: 'usage', label: 'Usage & Limits', icon: 'barChart' },
    { id: 'invoices', label: 'Invoices', icon: 'fileText' },
    { id: 'payments', label: 'Payment Methods', icon: 'dollarSign' },
    { id: 'settings', label: 'Billing Settings', icon: 'settings' }
  ];

  // Mock data - in a real app, this would come from API
  useEffect(() => {
    // Load current plan
    setCurrentPlan({
      id: 'pro',
      name: 'Professional',
      price: 49,
      currency: 'USD',
      interval: 'month',
      features: [
        'Up to 10,000 messages/month',
        'Advanced analytics',
        'Priority support',
        'Custom integrations',
        'Team collaboration'
      ],
      limits: {
        messages: 10000,
        users: 25,
        numbers: 10,
        campaigns: 50
      },
      nextBillingDate: '2024-02-15',
      status: 'active'
    });

    // Load usage data
    setUsageData({
      messages: { used: 7420, limit: 10000, percentage: 74.2 },
      users: { used: 12, limit: 25, percentage: 48 },
      numbers: { used: 6, limit: 10, percentage: 60 },
      campaigns: { used: 23, limit: 50, percentage: 46 },
      storage: { used: 2.4, limit: 10, percentage: 24, unit: 'GB' }
    });

    // Load invoices
    setInvoices([
      {
        id: 'inv-001',
        number: 'INV-2024-001',
        date: '2024-01-15',
        dueDate: '2024-01-30',
        amount: 49.00,
        currency: 'USD',
        status: 'paid',
        items: [
          { description: 'Professional Plan - January 2024', amount: 49.00 }
        ]
      },
      {
        id: 'inv-002',
        number: 'INV-2023-012',
        date: '2023-12-15',
        dueDate: '2023-12-30',
        amount: 49.00,
        currency: 'USD',
        status: 'paid',
        items: [
          { description: 'Professional Plan - December 2023', amount: 49.00 }
        ]
      }
    ]);

    // Load payment methods
    setPaymentMethods([
      {
        id: 'pm-001',
        type: 'card',
        brand: 'visa',
        last4: '4242',
        expiryMonth: 12,
        expiryYear: 2025,
        isDefault: true
      },
      {
        id: 'pm-002',
        type: 'card',
        brand: 'mastercard',
        last4: '5555',
        expiryMonth: 8,
        expiryYear: 2026,
        isDefault: false
      }
    ]);

    // Load billing alerts
    setBillingAlerts([
      {
        id: 'alert-001',
        type: 'usage',
        severity: 'warning',
        title: 'High Message Usage',
        message: 'You have used 74% of your monthly message limit.',
        threshold: 75,
        current: 74.2
      },
      {
        id: 'alert-002',
        type: 'billing',
        severity: 'info',
        title: 'Upcoming Renewal',
        message: 'Your subscription will renew on February 15, 2024.',
        date: '2024-02-15'
      }
    ]);
  }, []);

  const handlePlanChange = (newPlan) => {
    const remainingDays = 15; // Mock data
    const totalDaysInCycle = 30; // Mock data

    const dailyRateOld = currentPlan.price / totalDaysInCycle;
    const dailyRateNew = newPlan.price / totalDaysInCycle;

    const creditForOldPlan = dailyRateOld * remainingDays;
    const costForNewPlan = dailyRateNew * remainingDays;

    const proratedAmount = costForNewPlan - creditForOldPlan;

    setPlanChangePreview({
      newPlan,
      proratedAmount,
      creditForOldPlan,
      costForNewPlan,
    });

    setShowUpgradeModal(true);
  };

  const handlePlanUpgrade = (plan) => {
    handlePlanChange(plan);
  };

  const handlePlanDowngrade = (planId) => {
    console.log('Downgrading to plan:', planId);
    // Show confirmation dialog
    if (window.confirm('Are you sure you want to downgrade your plan? This will take effect at the end of your current billing cycle.')) {
      // Process downgrade
      console.log('Plan downgrade confirmed');
    }
  };

  const handleAddPaymentMethod = () => {
    setShowPaymentModal(true);
  };

  const handleRemovePaymentMethod = (methodId) => {
    if (window.confirm('Are you sure you want to remove this payment method?')) {
      setPaymentMethods(prev => prev.filter(pm => pm.id !== methodId));
    }
  };

  const handleSetDefaultPaymentMethod = (methodId) => {
    setPaymentMethods(prev => prev.map(pm => ({
      ...pm,
      isDefault: pm.id === methodId
    })));
  };

  const handleDownloadInvoice = (invoiceId) => {
    console.log('Downloading invoice:', invoiceId);
    // In a real app, this would generate and download the PDF
  };

  const handleExportBillingData = () => {
    const billingData = {
      currentPlan,
      usageData,
      invoices,
      paymentMethods: paymentMethods.map(pm => ({
        ...pm,
        // Remove sensitive data for export
        last4: pm.last4
      })),
      exportDate: new Date().toISOString()
    };

    const dataStr = JSON.stringify(billingData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `billing-data-${Date.now()}.json`;
    link.click();
    
    URL.revokeObjectURL(url);
  };

  const formatCurrency = (amount, currency = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const getUsageColor = (percentage) => {
    if (percentage >= 90) return 'red';
    if (percentage >= 75) return 'yellow';
    return 'green';
  };

  const renderOverview = () => (
    <div className="space-y-6">
      <BillingForecastWidget />
      {/* Billing Alerts */}
      {billingAlerts.length > 0 && (
        <div className="space-y-3">
          {billingAlerts.map(alert => (
            <div
              key={alert.id}
              className={`p-4 rounded-lg border-l-4 ${
                alert.severity === 'warning' 
                  ? 'bg-yellow-50 border-yellow-400' 
                  : alert.severity === 'error'
                    ? 'bg-red-50 border-red-400'
                    : 'bg-blue-50 border-blue-400'
              }`}
            >
              <div className="flex items-start space-x-3">
                <Icon 
                  name={alert.severity === 'warning' ? 'alertTriangle' : 'info'} 
                  size="sm" 
                  className={
                    alert.severity === 'warning' 
                      ? 'text-yellow-600' 
                      : alert.severity === 'error'
                        ? 'text-red-600'
                        : 'text-blue-600'
                  }
                />
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900">{alert.title}</h4>
                  <p className="text-sm text-gray-600 mt-1">{alert.message}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Current Plan Overview */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Current Plan</h3>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
            currentPlan?.status === 'active' 
              ? 'bg-green-100 text-green-800' 
              : 'bg-gray-100 text-gray-800'
          }`}>
            {currentPlan?.status}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="text-xl font-bold text-gray-900">{currentPlan?.name}</h4>
            <p className="text-3xl font-bold text-blue-600 mt-2">
              {formatCurrency(currentPlan?.price)}
              <span className="text-lg font-normal text-gray-600">/{currentPlan?.interval}</span>
            </p>
            <p className="text-sm text-gray-600 mt-2">
              Next billing date: {formatDate(currentPlan?.nextBillingDate)}
            </p>
          </div>

          <div>
            <h5 className="font-medium text-gray-900 mb-2">Plan Features</h5>
            <ul className="space-y-1">
              {currentPlan?.features.slice(0, 3).map((feature, index) => (
                <li key={index} className="flex items-center space-x-2 text-sm text-gray-600">
                  <Icon name="check" size="xs" className="text-green-500" />
                  <span>{feature}</span>
                </li>
              ))}
            </ul>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setActiveTab('plans')}
              className="mt-3"
            >
              View All Plans
            </Button>
          </div>
        </div>
      </div>

      {/* Usage Overview */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Usage Overview</h3>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setActiveTab('usage')}
          >
            View Details
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(usageData).map(([key, data]) => (
            <div key={key} className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700 capitalize">{key}</span>
                <span className="text-xs text-gray-500">
                  {data.used.toLocaleString()}{data.unit || ''} / {data.limit.toLocaleString()}{data.unit || ''}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full bg-${getUsageColor(data.percentage)}-500`}
                  style={{ width: `${Math.min(data.percentage, 100)}%` }}
                ></div>
              </div>
              <div className="flex justify-between items-center mt-1">
                <span className={`text-xs font-medium text-${getUsageColor(data.percentage)}-600`}>
                  {data.percentage.toFixed(1)}%
                </span>
                {data.percentage > 80 && (
                  <Icon name="alertTriangle" size="xs" className="text-yellow-500" />
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Invoices */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Recent Invoices</h3>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setActiveTab('invoices')}
          >
            View All
          </Button>
        </div>

        <div className="space-y-3">
          {invoices.slice(0, 3).map(invoice => (
            <div key={invoice.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <div className="font-medium text-gray-900">{invoice.number}</div>
                <div className="text-sm text-gray-600">{formatDate(invoice.date)}</div>
              </div>
              <div className="text-right">
                <div className="font-medium text-gray-900">{formatCurrency(invoice.amount)}</div>
                <div className={`text-sm ${
                  invoice.status === 'paid' ? 'text-green-600' : 'text-yellow-600'
                }`}>
                  {invoice.status}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderPlanChangePreviewModal = () => {
    if (!planChangePreview) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-md w-full">
          <h2 className="text-2xl font-bold mb-4">Confirm Plan Change</h2>
          <p className="mb-4">You are about to switch to the <strong>{planChangePreview.newPlan.name}</strong> plan.</p>
          
          <div className="bg-gray-100 p-4 rounded-lg mb-4">
            <div className="flex justify-between">
              <span>Credit for unused time on current plan:</span>
              <span>-{formatCurrency(planChangePreview.creditForOldPlan)}</span>
            </div>
            <div className="flex justify-between">
              <span>Cost for new plan for the rest of the cycle:</span>
              <span>{formatCurrency(planChangePreview.costForNewPlan)}</span>
            </div>
            <hr className="my-2" />
            <div className="flex justify-between font-bold">
              <span>Amount due today:</span>
              <span>{formatCurrency(planChangePreview.proratedAmount)}</span>
            </div>
          </div>

          <div className="flex justify-end space-x-4">
            <Button variant="outline" onClick={() => setShowUpgradeModal(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={() => {
              // Handle the actual upgrade here
              setShowUpgradeModal(false);
            }}>
              Confirm Upgrade
            </Button>
          </div>
        </div>
      </div>
    );
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return renderOverview();
      
      case 'plans':
        return (
          <SubscriptionPlans
            currentPlan={currentPlan}
            billingCycle={billingCycle}
            onBillingCycleChange={setBillingCycle}
            onPlanSelect={handlePlanUpgrade}
            onPlanDowngrade={handlePlanDowngrade}
          />
        );
      
      case 'usage':
        return (
          <UsageMetrics
            usageData={usageData}
            currentPlan={currentPlan}
            showAlerts={true}
            showProjections={true}
          />
        );
      
      case 'invoices':
        return (
          <InvoiceHistory
            invoices={invoices}
            onDownload={handleDownloadInvoice}
            showFilters={true}
            showExport={true}
          />
        );
      
      case 'payments':
        return (
          <PaymentMethods
            paymentMethods={paymentMethods}
            onAdd={handleAddPaymentMethod}
            onRemove={handleRemovePaymentMethod}
            onSetDefault={handleSetDefaultPaymentMethod}
          />
        );
      
      case 'settings':
        return (
          <div className="space-y-6">
            {/* Billing Settings */}
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Billing Settings</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Billing Cycle
                  </label>
                  <select
                    value={billingCycle}
                    onChange={(e) => setBillingCycle(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  >
                    <option value="monthly">Monthly</option>
                    <option value="yearly">Yearly (Save 20%)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Invoice Email
                  </label>
                  <input
                    type="email"
                    defaultValue="billing@company.com"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      defaultChecked
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700">
                      Send usage alerts when approaching limits
                    </span>
                  </label>
                </div>

                <div>
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      defaultChecked
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700">
                      Auto-renew subscription
                    </span>
                  </label>
                </div>
              </div>

              <div className="mt-6 pt-6 border-t border-gray-200">
                <Button variant="primary">
                  Save Settings
                </Button>
              </div>
            </div>

            {/* Data Export */}
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Data Export</h3>
              <p className="text-sm text-gray-600 mb-4">
                Export your billing data, invoices, and usage history.
              </p>
              
              <Button
                variant="outline"
                onClick={handleExportBillingData}
              >
                <Icon name="download" size="sm" className="mr-2" />
                Export Billing Data
              </Button>
            </div>

            {/* Danger Zone */}
            <div className="bg-white border border-red-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-red-900 mb-4">Danger Zone</h3>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-red-50 rounded-lg">
                  <div>
                    <h4 className="font-medium text-red-900">Cancel Subscription</h4>
                    <p className="text-sm text-red-700">
                      Cancel your subscription. You'll retain access until the end of your billing period.
                    </p>
                  </div>
                  <Button
                    variant="outline"
                    className="border-red-300 text-red-700 hover:bg-red-50"
                    onClick={() => {
                      if (window.confirm('Are you sure you want to cancel your subscription?')) {
                        console.log('Subscription cancelled');
                      }
                    }}
                  >
                    Cancel Plan
                  </Button>
                </div>
              </div>
            </div>
          </div>
        );
      
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      {renderPlanChangePreviewModal()}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Billing & Subscription</h1>
              <p className="text-gray-600 mt-2">
                Manage your subscription, view usage, and handle billing settings
              </p>
            </div>
            
            <div className="flex items-center space-x-3">
              <Button
                variant="outline"
                onClick={handleExportBillingData}
              >
                <Icon name="download" size="sm" className="mr-2" />
                Export Data
              </Button>
              
              <Button
                variant="primary"
                onClick={() => setActiveTab('plans')}
              >
                <Icon name="upgrade" size="sm" className="mr-2" />
                Upgrade Plan
              </Button>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="mb-8">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8 overflow-x-auto">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon name={tab.icon} size="sm" />
                  <span>{tab.label}</span>
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        <div className="space-y-8">
          {renderTabContent()}
        </div>
      </div>
    </div>
  );
};

export default BillingPage;