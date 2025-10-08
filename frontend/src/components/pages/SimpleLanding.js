import React from 'react';

const SimpleLanding = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Welcome to Namaskah.App
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Enterprise Communication Platform
          </p>
          <div className="space-x-4">
            <a 
              href="/login" 
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Login
            </a>
            <a 
              href="/register" 
              className="bg-gray-600 text-white px-6 py-3 rounded-lg hover:bg-gray-700 transition-colors"
            >
              Register
            </a>
          </div>
        </div>
        
        <div className="mt-16 grid md:grid-cols-3 gap-8">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-2">SMS Verification</h3>
            <p className="text-gray-600">Verify accounts across 100+ services</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-2">Real-time Chat</h3>
            <p className="text-gray-600">Instant messaging with WebSocket support</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-2">AI Assistant</h3>
            <p className="text-gray-600">Smart automation and conversation intelligence</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SimpleLanding;