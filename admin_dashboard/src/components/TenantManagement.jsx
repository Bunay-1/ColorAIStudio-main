import React, { useState, useEffect } from 'react'
import { Plus, Edit, Trash, Search, Users, Database } from 'lucide-react'

export default function TenantManagement() {
  const [tenants, setTenants] = useState([])
  const [searchTerm, setSearchTerm] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editingTenant, setEditingTenant] = useState(null)

  useEffect(() => {
    fetchTenants()
  }, [])

  const fetchTenants = async () => {
    try {
      const token = localStorage.getItem('icap_token')
      const response = await fetch('http://localhost:8000/auth/tenants', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setTenants(data.tenants || [])
      }
    } catch (error) {
      console.error('Error fetching tenants:', error)
    }
  }

  const filteredTenants = tenants.filter(tenant =>
    tenant.tenant_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    tenant.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const handleCreateTenant = () => {
    setEditingTenant(null)
    setShowModal(true)
  }

  const handleEditTenant = (tenant) => {
    setEditingTenant(tenant)
    setShowModal(true)
  }

  const handleDeleteTenant = async (tenantId) => {
    if (window.confirm('Are you sure you want to delete this tenant?')) {
      try {
        const token = localStorage.getItem('icap_token')
        await fetch(`http://localhost:8000/auth/tenants/${tenantId}`, {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${token}` }
        })
        fetchTenants()
      } catch (error) {
        console.error('Error deleting tenant:', error)
      }
    }
  }

  const handleActivateTenant = async (tenantId) => {
    try {
      const token = localStorage.getItem('icap_token')
      await fetch(`http://localhost:8000/auth/tenants/${tenantId}/activate`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      fetchTenants()
    } catch (error) {
      console.error('Error activating tenant:', error)
    }
  }

  const handleDeactivateTenant = async (tenantId) => {
    try {
      const token = localStorage.getItem('icap_token')
      await fetch(`http://localhost:8000/auth/tenants/${tenantId}/deactivate`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      fetchTenants()
    } catch (error) {
      console.error('Error deactivating tenant:', error)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Tenant Management</h1>
          <p className="text-gray-600 mt-1">Manage multi-tenant organization</p>
        </div>
        <button onClick={handleCreateTenant} className="btn-primary flex items-center space-x-2">
          <Plus size={20} />
          <span>Add Tenant</span>
        </button>
      </div>

      <div className="card">
        <div className="flex items-center space-x-4 mb-6">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Search tenants..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-field pl-10"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredTenants.map((tenant) => (
            <TenantCard
              key={tenant.tenant_id}
              tenant={tenant}
              onEdit={() => handleEditTenant(tenant)}
              onDelete={() => handleDeleteTenant(tenant.tenant_id)}
              onActivate={() => handleActivateTenant(tenant.tenant_id)}
              onDeactivate={() => handleDeactivateTenant(tenant.tenant_id)}
            />
          ))}
        </div>
      </div>

      {showModal && (
        <TenantModal
          tenant={editingTenant}
          onClose={() => setShowModal(false)}
          onSave={() => {
            setShowModal(false)
            fetchTenants()
          }}
        />
      )}
    </div>
  )
}

function TenantCard({ tenant, onEdit, onDelete, onActivate, onDeactivate }) {
  const config = tenant.config || {}
  
  return (
    <div className="card">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{tenant.name}</h3>
          <p className="text-sm text-gray-600">{tenant.tenant_id}</p>
        </div>
        <span className={`px-2 py-1 rounded text-sm ${
          tenant.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
        }`}>
          {tenant.is_active ? 'Active' : 'Inactive'}
        </span>
      </div>
      
      <div className="space-y-2 mb-4">
        <div className="flex items-center space-x-2 text-sm text-gray-600">
          <Users size={16} />
          <span>{config.max_users || 'Unlimited'} users</span>
        </div>
        <div className="flex items-center space-x-2 text-sm text-gray-600">
          <Database size={16} />
          <span>{config.storage_quota_gb || 'Unlimited'} GB</span>
        </div>
      </div>
      
      <div className="flex justify-end space-x-2">
        {tenant.is_active ? (
          <button onClick={onDeactivate} className="btn-secondary text-sm">
            Deactivate
          </button>
        ) : (
          <button onClick={onActivate} className="btn-primary text-sm">
            Activate
          </button>
        )}
        <button onClick={onEdit} className="btn-secondary text-sm">
          Edit
        </button>
        <button onClick={onDelete} className="btn-danger text-sm">
          Delete
        </button>
      </div>
    </div>
  )
}

function TenantModal({ tenant, onClose, onSave }) {
  const [formData, setFormData] = useState({
    tenant_id: tenant?.tenant_id || '',
    name: tenant?.name || '',
    config: tenant?.config || {
      max_users: 10,
      storage_quota_gb: 10
    }
  })

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      const token = localStorage.getItem('icap_token')
      const url = tenant 
        ? `http://localhost:8000/auth/tenants/${tenant.tenant_id}`
        : 'http://localhost:8000/auth/tenants'
      
      const method = tenant ? 'PUT' : 'POST'
      
      await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      })
      onSave()
    } catch (error) {
      console.error('Error saving tenant:', error)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 className="text-xl font-bold mb-4">
          {tenant ? 'Edit Tenant' : 'Create Tenant'}
        </h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tenant ID
            </label>
            <input
              type="text"
              value={formData.tenant_id}
              onChange={(e) => setFormData({...formData, tenant_id: e.target.value})}
              className="input-field"
              disabled={!!tenant}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Name
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              className="input-field"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Max Users
            </label>
            <input
              type="number"
              value={formData.config.max_users}
              onChange={(e) => setFormData({
                ...formData,
                config: {...formData.config, max_users: parseInt(e.target.value)}
              })}
              className="input-field"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Storage Quota (GB)
            </label>
            <input
              type="number"
              value={formData.config.storage_quota_gb}
              onChange={(e) => setFormData({
                ...formData,
                config: {...formData.config, storage_quota_gb: parseInt(e.target.value)}
              })}
              className="input-field"
            />
          </div>
          <div className="flex justify-end space-x-3">
            <button type="button" onClick={onClose} className="btn-secondary">
              Cancel
            </button>
            <button type="submit" className="btn-primary">
              Save
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
