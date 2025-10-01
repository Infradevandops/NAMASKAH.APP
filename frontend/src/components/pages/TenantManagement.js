import React, { useState, useEffect } from 'react';
import axios from 'axios';

const TenantManagement = () => {
  const [tenants, setTenants] = useState([]);
  const [currentTenant, setCurrentTenant] = useState(null);
  const [tenantUsers, setTenantUsers] = useState([]);
  const [tenantInvitations, setTenantInvitations] = useState([]);
  const [newTenant, setNewTenant] = useState({ name: '', description: '' });
  const [newInvitation, setNewInvitation] = useState({ email: '', role: 'member' });
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('tenants');
  const [showCreateForm, setShowCreateForm] = useState(false);

  useEffect(() => {
    fetchTenants();
    fetchCurrentTenant();
  }, []);

  const fetchTenants = async () => {
    try {
      const response = await axios.get('/api/tenants');
      setTenants(response.data.tenants || response.data);
    } catch (error) {
      console.error('Error fetching tenants:', error);
    }
  };

  const fetchCurrentTenant = async () => {
    try {
      const response = await axios.get('/api/tenants/current');
      setCurrentTenant(response.data);
      if (response.data) {
        fetchTenantUsers(response.data.id);
        fetchTenantInvitations(response.data.id);
      }
    } catch (error) {
      console.error('Error fetching current tenant:', error);
    }
  };

  const fetchTenantUsers = async (tenantId) => {
    try {
      const response = await axios.get(`/api/tenants/${tenantId}/users`);
      setTenantUsers(response.data.users || response.data);
    } catch (error) {
      console.error('Error fetching tenant users:', error);
    }
  };

  const fetchTenantInvitations = async (tenantId) => {
    try {
      const response = await axios.get(`/api/tenants/${tenantId}/invitations`);
      setTenantInvitations(response.data.invitations || response.data);
    } catch (error) {
      console.error('Error fetching tenant invitations:', error);
    }
  };

  const createTenant = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post('/api/tenants', newTenant);
      setNewTenant({ name: '', description: '' });
      setShowCreateForm(false);
      fetchTenants();
    } catch (error) {
      console.error('Error creating tenant:', error);
      alert('Error creating tenant: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const updateTenant = async (tenantId, updates) => {
    try {
      await axios.put(`/api/tenants/${tenantId}`, updates);
      fetchTenants();
      if (currentTenant?.id === tenantId) {
        fetchCurrentTenant();
      }
    } catch (error) {
      console.error('Error updating tenant:', error);
      alert('Error updating tenant: ' + (error.response?.data?.detail || error.message));
    }
  };

  const deleteTenant = async (tenantId) => {
    if (!confirm('Are you sure you want to delete this tenant? This action cannot be undone.')) {
      return;
    }
    try {
      await axios.delete(`/api/tenants/${tenantId}`);
      fetchTenants();
      if (currentTenant?.id === tenantId) {
        setCurrentTenant(null);
        setTenantUsers([]);
        setTenantInvitations([]);
      }
    } catch (error) {
      console.error('Error deleting tenant:', error);
      alert('Error deleting tenant: ' + (error.response?.data?.detail || error.message));
    }
  };

  const inviteUser = async (e) => {
    e.preventDefault();
    if (!currentTenant) return;

    setLoading(true);
    try {
      await axios.post(`/api/tenants/${currentTenant.id}/invitations`, newInvitation);
      setNewInvitation({ email: '', role: 'member' });
      fetchTenantInvitations(currentTenant.id);
    } catch (error) {
      console.error('Error inviting user:', error);
      alert('Error inviting user: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const cancelInvitation = async (invitationId) => {
    if (!currentTenant) return;

    try {
      await axios.delete(`/api/tenants/${currentTenant.id}/invitations/${invitationId}`);
      fetchTenantInvitations(currentTenant.id);
    } catch (error) {
      console.error('Error canceling invitation:', error);
      alert('Error canceling invitation: ' + (error.response?.data?.detail || error.message));
    }
  };

  const removeUser = async (userId) => {
    if (!currentTenant) return;

    if (!confirm('Are you sure you want to remove this user from the tenant?')) {
      return;
    }

    try {
      await axios.delete(`/api/tenants/${currentTenant.id}/users/${userId}`);
      fetchTenantUsers(currentTenant.id);
    } catch (error) {
      console.error('Error removing user:', error);
      alert('Error removing user: ' + (error.response?.data?.detail || error.message));
    }
  };

  const switchTenant = async (tenantId) => {
    try {
      await axios.post(`/api/tenants/${tenantId}/switch`);
      fetchCurrentTenant();
    } catch (error) {
      console.error('Error switching tenant:', error);
      alert('Error switching tenant: ' + (error.response?.data?.detail || error.message));
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Tenant Management</h1>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
        >
          {showCreateForm ? 'Cancel' : 'Create Tenant'}
        </button>
      </div>

      {/* Current Tenant Info */}
      {currentTenant && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <h2 className="text-lg font-semibold text-blue-800">Current Tenant</h2>
          <p className="text-blue-700"><strong>{currentTenant.name}</strong></p>
          <p className="text-blue-600 text-sm">{currentTenant.description}</p>
          <div className="mt-2 text-sm text-blue-600">
            <span>Created: {new Date(currentTenant.created_at).toLocaleDateString()}</span>
            <span className="ml-4">Users: {tenantUsers.length}</span>
          </div>
        </div>
      )}

      {/* Create Tenant Form */}
      {showCreateForm && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Create New Tenant</h2>
          <form onSubmit={createTenant} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Name</label>
              <input
                type="text"
                value={newTenant.name}
                onChange={(e) => setNewTenant({ ...newTenant, name: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Description</label>
              <textarea
                value={newTenant.description}
                onChange={(e) => setNewTenant({ ...newTenant, description: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                rows="3"
              />
            </div>
            <div className="flex space-x-4">
              <button
                type="submit"
                disabled={loading}
                className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 disabled:opacity-50"
              >
                {loading ? 'Creating...' : 'Create Tenant'}
              </button>
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="bg-gray-500 text-white px-4 py-2 rounded-md hover:bg-gray-600"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Tabs */}
      <div className="mb-6">
        <nav className="flex space-x-4">
          {[
            { id: 'tenants', label: 'All Tenants' },
            { id: 'users', label: 'Users' },
            { id: 'invitations', label: 'Invitations' },
            { id: 'settings', label: 'Settings' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 rounded-md ${
                activeTab === tab.id
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'tenants' && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">All Tenants</h2>
          <div className="space-y-4">
            {tenants.map((tenant) => (
              <div key={tenant.id} className="border rounded-lg p-4">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-lg font-medium">{tenant.name}</h3>
                    <p className="text-gray-600">{tenant.description}</p>
                    <div className="mt-2 text-sm text-gray-500">
                      <span>Created: {new Date(tenant.created_at).toLocaleDateString()}</span>
                      <span className="ml-4">Owner: {tenant.owner?.email || 'Unknown'}</span>
                    </div>
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => switchTenant(tenant.id)}
                      className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
                    >
                      Switch To
                    </button>
                    <button
                      onClick={() => updateTenant(tenant.id, { name: tenant.name, description: tenant.description })}
                      className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => deleteTenant(tenant.id)}
                      className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'users' && currentTenant && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Tenant Users</h2>
          <div className="space-y-4">
            {tenantUsers.map((user) => (
              <div key={user.id} className="border rounded-lg p-4">
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="font-medium">{user.first_name} {user.last_name}</h3>
                    <p className="text-gray-600">{user.email}</p>
                    <div className="mt-1">
                      <span className="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded">
                        {user.role || 'member'}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => removeUser(user.id)}
                    className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                  >
                    Remove
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'invitations' && currentTenant && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Pending Invitations</h2>

          {/* Invite User Form */}
          <form onSubmit={inviteUser} className="mb-6 p-4 bg-gray-50 rounded-lg">
            <h3 className="font-medium mb-3">Invite New User</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Email</label>
                <input
                  type="email"
                  value={newInvitation.email}
                  onChange={(e) => setNewInvitation({ ...newInvitation, email: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Role</label>
                <select
                  value={newInvitation.role}
                  onChange={(e) => setNewInvitation({ ...newInvitation, role: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                >
                  <option value="member">Member</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div className="flex items-end">
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 disabled:opacity-50"
                >
                  {loading ? 'Inviting...' : 'Send Invitation'}
                </button>
              </div>
            </div>
          </form>

          {/* Invitations List */}
          <div className="space-y-4">
            {tenantInvitations.map((invitation) => (
              <div key={invitation.id} className="border rounded-lg p-4">
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="font-medium">{invitation.email}</h3>
                    <p className="text-gray-600">Role: {invitation.role}</p>
                    <p className="text-sm text-gray-500">
                      Invited: {new Date(invitation.created_at).toLocaleDateString()}
                      {invitation.expires_at && ` • Expires: ${new Date(invitation.expires_at).toLocaleDateString()}`}
                    </p>
                    <span className={`text-sm px-2 py-1 rounded ${
                      invitation.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                      invitation.status === 'accepted' ? 'bg-green-100 text-green-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {invitation.status}
                    </span>
                  </div>
                  {invitation.status === 'pending' && (
                    <button
                      onClick={() => cancelInvitation(invitation.id)}
                      className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                    >
                      Cancel
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'settings' && currentTenant && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Tenant Settings</h2>
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700">Tenant Name</label>
              <input
                type="text"
                value={currentTenant.name}
                onChange={(e) => setCurrentTenant({ ...currentTenant, name: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Description</label>
              <textarea
                value={currentTenant.description || ''}
                onChange={(e) => setCurrentTenant({ ...currentTenant, description: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                rows="3"
              />
            </div>
            <button
              onClick={() => updateTenant(currentTenant.id, {
                name: currentTenant.name,
                description: currentTenant.description
              })}
              className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
            >
              Save Changes
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default TenantManagement;
