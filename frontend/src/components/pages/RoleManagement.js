import React, { useState, useEffect } from 'react';
import axios from 'axios';

const RoleManagement = () => {
  const [roles, setRoles] = useState([]);
  const [permissions, setPermissions] = useState([]);
  const [users, setUsers] = useState([]);
  const [rolePermissions, setRolePermissions] = useState({});
  const [userRoles, setUserRoles] = useState({});
  const [newRole, setNewRole] = useState({ name: '', description: '' });
  const [newPermission, setNewPermission] = useState({ name: '', resource: '', action: '', description: '' });
  const [selectedRole, setSelectedRole] = useState(null);
  const [selectedUser, setSelectedUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('roles');
  const [showCreateForm, setShowCreateForm] = useState(false);

  useEffect(() => {
    fetchRoles();
    fetchPermissions();
    fetchUsers();
  }, []);

  const fetchRoles = async () => {
    try {
      const response = await axios.get('/api/rbac/roles');
      setRoles(response.data);
    } catch (error) {
      console.error('Error fetching roles:', error);
    }
  };

  const fetchPermissions = async () => {
    try {
      const response = await axios.get('/api/rbac/permissions');
      setPermissions(response.data);
    } catch (error) {
      console.error('Error fetching permissions:', error);
    }
  };

  const fetchUsers = async () => {
    try {
      // This would need to be implemented in the backend
      // For now, we'll use a placeholder
      setUsers([]);
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  };

  const fetchRolePermissions = async (roleId) => {
    try {
      const response = await axios.get(`/api/rbac/roles/${roleId}/permissions`);
      setRolePermissions(prev => ({ ...prev, [roleId]: response.data }));
    } catch (error) {
      console.error('Error fetching role permissions:', error);
    }
  };

  const fetchUserRoles = async (userId) => {
    try {
      const response = await axios.get(`/api/rbac/users/${userId}/roles`);
      setUserRoles(prev => ({ ...prev, [userId]: response.data }));
    } catch (error) {
      console.error('Error fetching user roles:', error);
    }
  };

  const createRole = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post('/api/rbac/roles', newRole);
      setNewRole({ name: '', description: '' });
      setShowCreateForm(false);
      fetchRoles();
    } catch (error) {
      console.error('Error creating role:', error);
      alert('Error creating role: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const createPermission = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post('/api/rbac/permissions', newPermission);
      setNewPermission({ name: '', resource: '', action: '', description: '' });
      fetchPermissions();
    } catch (error) {
      console.error('Error creating permission:', error);
      alert('Error creating permission: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const assignPermissionToRole = async (roleId, permissionId) => {
    try {
      await axios.post(`/api/rbac/roles/${roleId}/permissions`, { permission_id: permissionId });
      fetchRolePermissions(roleId);
    } catch (error) {
      console.error('Error assigning permission:', error);
      alert('Error assigning permission: ' + (error.response?.data?.detail || error.message));
    }
  };

  const removePermissionFromRole = async (roleId, permissionId) => {
    try {
      await axios.delete(`/api/rbac/roles/${roleId}/permissions/${permissionId}`);
      fetchRolePermissions(roleId);
    } catch (error) {
      console.error('Error removing permission:', error);
      alert('Error removing permission: ' + (error.response?.data?.detail || error.message));
    }
  };

  const assignRoleToUser = async (userId, roleId) => {
    try {
      await axios.post(`/api/rbac/users/${userId}/roles`, { role_id: roleId });
      fetchUserRoles(userId);
    } catch (error) {
      console.error('Error assigning role:', error);
      alert('Error assigning role: ' + (error.response?.data?.detail || error.message));
    }
  };

  const removeRoleFromUser = async (userId, roleId) => {
    try {
      await axios.delete(`/api/rbac/users/${userId}/roles/${roleId}`);
      fetchUserRoles(userId);
    } catch (error) {
      console.error('Error removing role:', error);
      alert('Error removing role: ' + (error.response?.data?.detail || error.message));
    }
  };

  const updateRole = async (roleId, updates) => {
    try {
      await axios.put(`/api/rbac/roles/${roleId}`, updates);
      fetchRoles();
    } catch (error) {
      console.error('Error updating role:', error);
      alert('Error updating role: ' + (error.response?.data?.detail || error.message));
    }
  };

  const deactivateRole = async (roleId) => {
    if (!confirm('Are you sure you want to deactivate this role?')) {
      return;
    }
    try {
      await axios.delete(`/api/rbac/roles/${roleId}`);
      fetchRoles();
    } catch (error) {
      console.error('Error deactivating role:', error);
      alert('Error deactivating role: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleRoleSelect = (role) => {
    setSelectedRole(role);
    fetchRolePermissions(role.id);
  };

  const handleUserSelect = (user) => {
    setSelectedUser(user);
    fetchUserRoles(user.id);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Role-Based Access Control</h1>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
        >
          {showCreateForm ? 'Cancel' : 'Create Role'}
        </button>
      </div>

      {/* Create Role Form */}
      {showCreateForm && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Create New Role</h2>
          <form onSubmit={createRole} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Role Name</label>
              <input
                type="text"
                value={newRole.name}
                onChange={(e) => setNewRole({ ...newRole, name: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Description</label>
              <textarea
                value={newRole.description}
                onChange={(e) => setNewRole({ ...newRole, description: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                rows="2"
              />
            </div>
            <div className="flex space-x-4">
              <button
                type="submit"
                disabled={loading}
                className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 disabled:opacity-50"
              >
                {loading ? 'Creating...' : 'Create Role'}
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
            { id: 'roles', label: 'Roles' },
            { id: 'permissions', label: 'Permissions' },
            { id: 'assignments', label: 'Assignments' },
            { id: 'users', label: 'User Roles' }
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
      {activeTab === 'roles' && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Roles</h2>
          <div className="space-y-4">
            {roles.map((role) => (
              <div key={role.id} className="border rounded-lg p-4">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h3 className="text-lg font-medium">{role.name}</h3>
                    <p className="text-gray-600">{role.description}</p>
                    <div className="mt-2 text-sm text-gray-500">
                      <span>Created: {new Date(role.created_at).toLocaleDateString()}</span>
                      <span className="ml-4">
                        Status: <span className={`px-2 py-1 rounded text-xs ${
                          role.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {role.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </span>
                      {role.is_system_role && (
                        <span className="ml-4">
                          <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                            System Role
                          </span>
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex space-x-2 ml-4">
                    <button
                      onClick={() => handleRoleSelect(role)}
                      className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
                    >
                      Manage
                    </button>
                    {!role.is_system_role && (
                      <>
                        <button
                          onClick={() => updateRole(role.id, { name: role.name, description: role.description })}
                          className="bg-yellow-600 text-white px-3 py-1 rounded text-sm hover:bg-yellow-700"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => deactivateRole(role.id)}
                          className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                        >
                          Deactivate
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'permissions' && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Permissions</h2>

          {/* Create Permission Form */}
          <form onSubmit={createPermission} className="mb-6 p-4 bg-gray-50 rounded-lg">
            <h3 className="font-medium mb-3">Create New Permission</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Permission Name</label>
                <input
                  type="text"
                  value={newPermission.name}
                  onChange={(e) => setNewPermission({ ...newPermission, name: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Resource</label>
                <input
                  type="text"
                  value={newPermission.resource}
                  onChange={(e) => setNewPermission({ ...newPermission, resource: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Action</label>
                <input
                  type="text"
                  value={newPermission.action}
                  onChange={(e) => setNewPermission({ ...newPermission, action: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Description</label>
                <input
                  type="text"
                  value={newPermission.description}
                  onChange={(e) => setNewPermission({ ...newPermission, description: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                />
              </div>
              <div className="md:col-span-2 flex justify-end">
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 disabled:opacity-50"
                >
                  {loading ? 'Creating...' : 'Create Permission'}
                </button>
              </div>
            </div>
          </form>

          {/* Permissions List */}
          <div className="space-y-4">
            {permissions.map((permission) => (
              <div key={permission.id} className="border rounded-lg p-4">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-medium">{permission.name}</h3>
                    <p className="text-gray-600">{permission.description}</p>
                    <div className="mt-2 text-sm text-gray-500">
                      <span>Resource: {permission.resource}</span>
                      <span className="ml-4">Action: {permission.action}</span>
                      {permission.is_system_permission && (
                        <span className="ml-4">
                          <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                            System Permission
                          </span>
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'assignments' && selectedRole && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Manage Permissions for "{selectedRole.name}"</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Current Permissions */}
            <div>
              <h3 className="text-lg font-medium mb-3">Current Permissions</h3>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {(rolePermissions[selectedRole.id] || []).map((permission) => (
                  <div key={permission.id} className="flex justify-between items-center bg-green-50 p-3 rounded">
                    <div>
                      <span className="font-medium">{permission.name}</span>
                      <span className="text-sm text-gray-600 ml-2">
                        ({permission.resource}.{permission.action})
                      </span>
                    </div>
                    <button
                      onClick={() => removePermissionFromRole(selectedRole.id, permission.id)}
                      className="text-red-600 hover:text-red-800"
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Available Permissions */}
            <div>
              <h3 className="text-lg font-medium mb-3">Available Permissions</h3>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {permissions
                  .filter(perm => !(rolePermissions[selectedRole.id] || []).find(rp => rp.id === perm.id))
                  .map((permission) => (
                    <div key={permission.id} className="flex justify-between items-center bg-gray-50 p-3 rounded">
                      <div>
                        <span className="font-medium">{permission.name}</span>
                        <span className="text-sm text-gray-600 ml-2">
                          ({permission.resource}.{permission.action})
                        </span>
                      </div>
                      <button
                        onClick={() => assignPermissionToRole(selectedRole.id, permission.id)}
                        className="text-green-600 hover:text-green-800"
                      >
                        Add
                      </button>
                    </div>
                  ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'users' && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">User Role Assignments</h2>
          <div className="text-center text-gray-500">
            User role management functionality would be implemented here.
            This requires backend API endpoints for user management within tenants.
          </div>
        </div>
      )}
    </div>
  );
};

export default RoleManagement;
