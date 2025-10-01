import React, { useEffect, useState } from 'react';
import axios from 'axios';
import LoadingSpinner from '../atoms/LoadingSpinner';

const VerificationDashboard = () => {
  const [verifications, setVerifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch verification history
  const fetchVerifications = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get('/api/verification/history');
      setVerifications(response.data);
    } catch (err) {
      setError(err.message || 'Failed to load verification history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVerifications();
  }, []);

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

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Verification Dashboard</h1>
      {verifications.length === 0 ? (
        <p>No verification records found.</p>
      ) : (
        <table className="min-w-full border border-gray-300 rounded">
          <thead>
            <tr className="bg-gray-100">
              <th className="border px-4 py-2 text-left">ID</th>
              <th className="border px-4 py-2 text-left">Status</th>
              <th className="border px-4 py-2 text-left">Created At</th>
              <th className="border px-4 py-2 text-left">Completed At</th>
            </tr>
          </thead>
          <tbody>
            {verifications.map((v) => (
              <tr key={v.id} className="hover:bg-gray-50">
                <td className="border px-4 py-2">{v.id}</td>
                <td className="border px-4 py-2">{v.status}</td>
                <td className="border px-4 py-2">{new Date(v.created_at).toLocaleString()}</td>
                <td className="border px-4 py-2">{v.completed_at ? new Date(v.completed_at).toLocaleString() : '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default VerificationDashboard;
