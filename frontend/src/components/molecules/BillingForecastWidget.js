import React from 'react';

const BillingForecastWidget = () => {
  return (
    <div className="bg-white p-4 rounded-lg shadow-md">
      <h3 className="text-lg font-semibold mb-2">Billing Forecast</h3>
      <p className="text-gray-600">Your estimated cost for the next billing cycle is:</p>
      <p className="text-2xl font-bold text-gray-800">$XX.XX</p>
      <p className="text-sm text-gray-500 mt-2">This is an estimate based on your current usage and subscription plan.</p>
    </div>
  );
};

export default BillingForecastWidget;
