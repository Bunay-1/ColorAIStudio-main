import React, { useState, useEffect } from 'react'
import { Activity, Cpu, HardDrive, Memory, Network, Server, CheckCircle, XCircle, AlertTriangle } from 'lucide-react'

export default function SystemHealth() {
  const [healthData, setHealthData] = useState({
    overall: 'healthy',
    services: [],
    resources: {
      cpu: 0,
      memory: 0,
      disk: 0,
      network: 0
    }
  })

  useEffect(() => {
    fetchHealthData()
    const interval = setInterval(fetchHealthData, 30000) // Refresh every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const fetchHealthData = async () => {
    try {
      const response = await fetch('http://localhost:8000/health')
      if (response.ok) {
        const data = await response.json()
        setHealthData(data)
      }
    } catch (error) {
      console.error('Error fetching health data:', error)
    }
  }

  const statusColors = {
    healthy: 'text-green-600 bg-green-100',
    degraded: 'text-yellow-600 bg-yellow-100',
    unhealthy: 'text-red-600 bg-red-100'
  }

  const statusIcons = {
    healthy: <CheckCircle size={20} className="text-green-600" />,
    degraded: <AlertTriangle size={20} className="text-yellow-600" />,
    unhealthy: <XCircle size={20} className="text-red-600" />
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">System Health</h1>
        <p className="text-gray-600 mt-1">Monitor system performance and service status</p>
      </div>

      {/* Overall Status */}
      <div className="card">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {statusIcons[healthData.overall]}
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Overall Status</h2>
              <p className="text-gray-600 capitalize">{healthData.overall}</p>
            </div>
          </div>
          <span className={`px-4 py-2 rounded-full text-sm font-medium ${statusColors[healthData.overall]}`}>
            {healthData.overall.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Resource Usage */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <ResourceCard
          icon={<Cpu className="text-primary-600" />}
          title="CPU Usage"
          value={healthData.resources.cpu}
          unit="%"
          color="primary"
        />
        <ResourceCard
          icon={<Memory className="text-primary-600" />}
          title="Memory Usage"
          value={healthData.resources.memory}
          unit="%"
          color="primary"
        />
        <ResourceCard
          icon={<HardDrive className="text-primary-600" />}
          title="Disk Usage"
          value={healthData.resources.disk}
          unit="%"
          color="primary"
        />
        <ResourceCard
          icon={<Network className="text-primary-600" />}
          title="Network"
          value={healthData.resources.network}
          unit="Mbps"
          color="primary"
        />
      </div>

      {/* Services Status */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Services Status</h3>
        <div className="space-y-3">
          {healthData.services.map((service) => (
            <ServiceCard key={service.name} {...service} />
          ))}
        </div>
      </div>

      {/* System Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">API Performance</h3>
          <div className="space-y-4">
            <MetricRow label="Average Response Time" value="120ms" status="good" />
            <MetricRow label="P95 Response Time" value="250ms" status="good" />
            <MetricRow label="P99 Response Time" value="450ms" status="warning" />
            <MetricRow label="Error Rate" value="0.02%" status="good" />
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Database Status</h3>
          <div className="space-y-4">
            <MetricRow label="Connections" value="45/100" status="good" />
            <MetricRow label="Query Latency" value="15ms" status="good" />
            <MetricRow label="Cache Hit Rate" value="85%" status="good" />
            <MetricRow label="Replication Lag" value="0ms" status="good" />
          </div>
        </div>
      </div>
    </div>
  )
}

function ResourceCard({ icon, title, value, unit, color }) {
  const getColorClass = (color) => {
    const colors = {
      primary: 'bg-primary-500',
      green: 'bg-green-500',
      yellow: 'bg-yellow-500',
      red: 'bg-red-500'
    }
    return colors[color] || colors.primary
  }

  return (
    <div className="card">
      <div className="flex items-center space-x-3 mb-4">
        <div className="p-3 bg-primary-50 rounded-lg">
          {icon}
        </div>
        <div>
          <p className="text-sm text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">
            {value}{unit}
          </p>
        </div>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`${getColorClass(color)} h-2 rounded-full transition-all`}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  )
}

function ServiceCard({ name, status, uptime, lastCheck }) {
  const statusColors = {
    running: 'text-green-600 bg-green-100',
    stopped: 'text-red-600 bg-red-100',
    degraded: 'text-yellow-600 bg-yellow-100'
  }

  const statusIcons = {
    running: <CheckCircle size={16} className="text-green-600" />,
    stopped: <XCircle size={16} className="text-red-600" />,
    degraded: <AlertTriangle size={16} className="text-yellow-600" />
  }

  return (
    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
      <div className="flex items-center space-x-3">
        <Server size={20} className="text-gray-400" />
        <div>
          <p className="font-medium text-gray-900">{name}</p>
          <p className="text-sm text-gray-600">Uptime: {uptime}</p>
        </div>
      </div>
      <div className="flex items-center space-x-3">
        <span className={`px-2 py-1 rounded text-sm ${statusColors[status]}`}>
          {status}
        </span>
        {statusIcons[status]}
      </div>
    </div>
  )
}

function MetricRow({ label, value, status }) {
  const statusColors = {
    good: 'text-green-600',
    warning: 'text-yellow-600',
    error: 'text-red-600'
  }

  return (
    <div className="flex justify-between items-center">
      <span className="text-gray-600">{label}</span>
      <span className={`font-semibold ${statusColors[status]}`}>{value}</span>
    </div>
  )
}
