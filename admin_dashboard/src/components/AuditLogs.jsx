import React, { useState, useEffect } from 'react'
import { Search, Filter, Download, Calendar, User, Shield, AlertTriangle } from 'lucide-react'
import { format } from 'date-fns'

export default function AuditLogs() {
  const [logs, setLogs] = useState([])
  const [searchTerm, setSearchTerm] = useState('')
  const [filterAction, setFilterAction] = useState('')
  const [filterSeverity, setFilterSeverity] = useState('')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)

  useEffect(() => {
    fetchAuditLogs()
  }, [page, filterAction, filterSeverity])

  const fetchAuditLogs = async () => {
    try {
      const token = localStorage.getItem('icap_token')
      const params = new URLSearchParams({
        limit: '50',
        page: page.toString()
      })
      
      if (filterAction) params.append('action', filterAction)
      if (filterSeverity) params.append('severity', filterSeverity)
      
      const response = await fetch(`http://localhost:8000/auth/audit/logs?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      
      if (response.ok) {
        const data = await response.json()
        setLogs(data.logs || [])
        setTotalPages(data.total_pages || 1)
      }
    } catch (error) {
      console.error('Error fetching audit logs:', error)
    }
  }

  const filteredLogs = logs.filter(log =>
    log.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
    log.user_id.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const severityColors = {
    INFO: 'bg-blue-100 text-blue-700',
    WARNING: 'bg-yellow-100 text-yellow-700',
    ERROR: 'bg-red-100 text-red-700',
    CRITICAL: 'bg-red-200 text-red-900'
  }

  const severityIcons = {
    INFO: <Shield size={16} className="text-blue-500" />,
    WARNING: <AlertTriangle size={16} className="text-yellow-500" />,
    ERROR: <AlertTriangle size={16} className="text-red-500" />,
    CRITICAL: <AlertTriangle size={16} className="text-red-700" />
  }

  const handleExport = () => {
    const csv = [
      ['Timestamp', 'Action', 'User', 'Role', 'Tenant', 'Severity', 'IP Address'],
      ...filteredLogs.map(log => [
        log.timestamp,
        log.action,
        log.user_id,
        log.user_role,
        log.tenant_id,
        log.severity,
        log.ip_address
      ])
    ].map(row => row.join(',')).join('\n')
    
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `audit_logs_${format(new Date(), 'yyyy-MM-dd')}.csv`
    a.click()
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Audit Logs</h1>
          <p className="text-gray-600 mt-1">View and filter system audit trail</p>
        </div>
        <button onClick={handleExport} className="btn-secondary flex items-center space-x-2">
          <Download size={20} />
          <span>Export</span>
        </button>
      </div>

      <div className="card">
        <div className="flex flex-wrap items-center gap-4 mb-6">
          <div className="flex-1 min-w-64 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Search logs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-field pl-10"
            />
          </div>
          
          <select
            value={filterAction}
            onChange={(e) => setFilterAction(e.target.value)}
            className="input-field"
          >
            <option value="">All Actions</option>
            <option value="login">Login</option>
            <option value="user_create">User Create</option>
            <option value="tenant_create">Tenant Create</option>
            <option value="data_access">Data Access</option>
          </select>
          
          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
            className="input-field"
          >
            <option value="">All Severities</option>
            <option value="INFO">INFO</option>
            <option value="WARNING">WARNING</option>
            <option value="ERROR">ERROR</option>
            <option value="CRITICAL">CRITICAL</option>
          </select>
          
          <button className="btn-secondary flex items-center space-x-2">
            <Filter size={20} />
            <span>More Filters</span>
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left py-3 px-4 font-semibold text-gray-900">Timestamp</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-900">Action</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-900">User</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-900">Role</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-900">Tenant</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-900">Severity</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-900">IP Address</th>
              </tr>
            </thead>
            <tbody>
              {filteredLogs.map((log, index) => (
                <tr key={index} className="border-b hover:bg-gray-50">
                  <td className="py-3 px-4 text-sm">
                    <div className="flex items-center space-x-2">
                      <Calendar size={16} className="text-gray-400" />
                      <span>{log.timestamp}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4">{log.action}</td>
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-2">
                      <User size={16} className="text-gray-400" />
                      <span>{log.user_id}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4">{log.user_role}</td>
                  <td className="py-3 px-4">{log.tenant_id}</td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-1 rounded text-sm flex items-center space-x-1 w-fit ${severityColors[log.severity]}`}>
                      {severityIcons[log.severity]}
                      <span>{log.severity}</span>
                    </span>
                  </td>
                  <td className="py-3 px-4 text-sm text-gray-600">{log.ip_address}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {totalPages > 1 && (
          <div className="flex justify-center items-center space-x-2 mt-6">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
              className="btn-secondary disabled:opacity-50"
            >
              Previous
            </button>
            <span className="text-gray-600">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page === totalPages}
              className="btn-secondary disabled:opacity-50"
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
