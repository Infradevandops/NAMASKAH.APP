import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Bar, Line, Pie } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

const EnterpriseAnalytics = () => {
  const [analytics, setAnalytics] = useState({
    tenants: [],
    roles: [],
    calls: [],
    routing: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const [tenantsRes, rolesRes, callsRes, routingRes] = await Promise.all([
        axios.get('/api/tenants'),
        axios.get('/api/rbac/roles'),
        axios.get('/api/calls'),
        axios.get('/api/routing/history')
      ]);

      setAnalytics({
        tenants: tenantsRes.data,
        roles: rolesRes.data,
        calls: callsRes.data,
        routing: routingRes.data
      });
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const tenantChartData = {
    labels: analytics.tenants.map(t => t.name),
    datasets: [{
      label: 'Tenants',
      data: analytics.tenants.map(t => t.users?.length || 0),
      backgroundColor: 'rgba(54, 162, 235, 0.5)',
      borderColor: 'rgba(54, 162, 235, 1)',
      borderWidth: 1,
    }],
  };

  const roleChartData = {
    labels: analytics.roles.map(r => r.name),
    datasets: [{
      label: 'Roles',
      data: analytics.roles.map(r => r.permissions?.length || 0),
      backgroundColor: 'rgba(255, 99, 132, 0.5)',
      borderColor: 'rgba(255, 99, 132, 1)',
      borderWidth: 1,
    }],
  };

  const callChartData = {
    labels: ['Voice Calls', 'Video Calls'],
    datasets: [{
      data: [
        analytics.calls.filter(c => c.call_type === 'voice').length,
        analytics.calls.filter(c => c.call_type === 'video').length,
      ],
      backgroundColor: ['rgba(75, 192, 192, 0.5)', 'rgba(255, 205, 86, 0.5)'],
      borderColor: ['rgba(75, 192, 192, 1)', 'rgba(255, 205, 86, 1)'],
      borderWidth: 1,
    }],
  };

  const routingChartData = {
    labels: analytics.routing.map(r => new Date(r.created_at).toLocaleDateString()),
    datasets: [{
      label: 'Routing Confidence',
      data: analytics.routing.map(r => r.confidence_score || 0),
      borderColor: 'rgba(153, 102, 255, 1)',
      backgroundColor: 'rgba(153, 102, 255, 0.2)',
      tension: 0.1,
    }],
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64">Loading analytics...</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Enterprise Analytics</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-700">Total Tenants</h3>
          <p className="text-3xl font-bold text-blue-600">{analytics.tenants.length}</p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-700">Total Roles</h3>
          <p className="text-3xl font-bold text-red-600">{analytics.roles.length}</p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-700">Total Calls</h3>
          <p className="text-3xl font-bold text-green-600">{analytics.calls.length}</p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-700">Routing Decisions</h3>
          <p className="text-3xl font-bold text-purple-600">{analytics.routing.length}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Tenant Distribution</h2>
          <Bar data={tenantChartData} />
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Role Permissions</h2>
          <Bar data={roleChartData} />
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Call Types</h2>
          <Pie data={callChartData} />
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">AI Routing Confidence</h2>
          <Line data={routingChartData} />
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6 mt-8">
        <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
        <div className="space-y-4">
          {analytics.routing.slice(0, 5).map((item, index) => (
            <div key={index} className="flex justify-between items-center border-b pb-2">
              <div>
                <p className="font-medium">Route: {item.route_taken}</p>
                <p className="text-sm text-gray-600">
                  Confidence: {(item.confidence_score * 100).toFixed(1)}%
                </p>
              </div>
              <span className="text-sm text-gray-500">
                {new Date(item.created_at).toLocaleString()}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default EnterpriseAnalytics;
