import React, { useState, useEffect } from 'react'
import { 
  Users, 
  Building2, 
  Activity, 
  Shield, 
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Clock
} from 'lucide-react'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export default function Dashboard() {
  const [stats, setStats] = useState({
    totalUsers: 0,
    totalTenants: 0,
    activeUsers: 0,
    systemHealth: 0,
    apiRequests: 0,
    errorRate: 0
  })
  const [recentActivity, setRecentActivity] = useState([])
  const [alerts, setAlerts] = useState([])

  useEffect(() => {
    // Fetch dashboard data
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      // In a real implementation, this would fetch from the API
      setStats({
        totalUsers: 156,
        totalTenants: 12,
        activeUsers: 89,
        systemHealth: 98,
        apiRequests: 45230,
        errorRate: 0.02
      })
      
      setRecentActivity([
        { id: 1, action: 'User login', user: 'admin', time: '2 min ago', type: 'info' },
        { id: 2, action: 'Color analysis', user: 'operator1', time: '5 min ago', type: 'success' },
        { id: 3, action: 'Tenant created', user: 'admin', time: '15 min ago', type: 'info' },
        { id: 4, action: 'Rate limit exceeded', user: 'user123', time: '20 min ago', type: 'warning' },
        { id: 5, action: 'Vision analysis', user: 'operator2', time: '25 min ago', type: 'success' },
      ])
      
      setAlerts([
        { id: 1, severity: 'warning', message: 'High memory usage on server-1', time: '10 min ago' },
        { id: 2, severity: 'info', message: 'Scheduled maintenance in 2 hours', time: '1 hour ago' },
      ])
    } catch (error) {
      console.error('Error fetching dashboard data:', error)
    }
  }

  const apiRequestsData = [
    { name: 'Mon', requests: 4000 },
    { name: 'Tue', requests: 3000 },
    { name: 'Wed', requests: 5000 },
    { name: 'Thu', requests: 4500 },
    { name: 'Fri', requests: 6000 },
    { name: 'Sat', requests: 3500 },
    { name: 'Sun', requests: 4000 },
  ]

  const responseTimeData = [
    { name: 'Mon', time: 120 },
    { name: 'Tue', time: 110 },
    { name: 'Wed', time: 130 },
    { name: 'Thu', time: 115 },
    { name: 'Fri', time: 140 },
    { name: 'Sat', time: 100 },
    { name: 'Sun', time: 105 },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">Overview of ICAP Enterprise system</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <StatCard
          icon={<Users className="text-primary-600" />}
          title="Total Users"
          value={stats.totalUsers}
          change="+12%"
          changeType="positive"
        />
        <StatCard
          icon={<Building2 className="text-primary-600" />}
          title="Total Tenants"
          value={stats.totalTenants}
          change="+2"
          changeType="positive"
        />
        <StatCard
          icon={<Activity className="text-primary-600" />}
          title="Active Users"
          value={stats.activeUsers}
          change="+5%"
          changeType="positive"
        />
        <StatCard
          icon={<Shield className="text-green-600" />}
          title="System Health"
          value={`${stats.systemHealth}%`}
          change="+2%"
          changeType="positive"
        />
        <StatCard
          icon={<TrendingUp className="text-primary-600" />}
          title="API Requests"
          value={stats.apiRequests.toLocaleString()}
          change="+18%"
          changeType="positive"
        />
        <StatCard
          icon={<AlertTriangle className="text-yellow-600" />}
          title="Error Rate"
          value={`${(stats.errorRate * 100).toFixed(2)}%`}
          change="-0.1%"
          changeType="positive"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">API Requests (Last 7 Days)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={apiRequestsData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="requests" fill="#0ea5e9" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Average Response Time (ms)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={responseTimeData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="time" stroke="#0ea5e9" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Activity and Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Recent Activity</h3>
          <div className="space-y-3">
            {recentActivity.map((activity) => (
              <ActivityItem key={activity.id} {...activity} />
            ))}
          </div>
        </div>
        
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Active Alerts</h3>
          <div className="space-y-3">
            {alerts.length === 0 ? (
              <p className="text-gray-500 text-center py-4">No active alerts</p>
            ) : (
              alerts.map((alert) => (
                <AlertItem key={alert.id} {...alert} />
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function StatCard({ icon, title, value, change, changeType }) {
  const changeColor = changeType === 'positive' ? 'text-green-600' : 'text-red-600'
  const changeIcon = changeType === 'positive' ? '↑' : '↓'
  
  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-3 bg-primary-50 rounded-lg">
            {icon}
          </div>
          <div>
            <p className="text-sm text-gray-600">{title}</p>
            <p className="text-2xl font-bold text-gray-900">{value}</p>
          </div>
        </div>
        <div className={`text-sm ${changeColor}`}>
          {changeIcon} {change}
        </div>
      </div>
    </div>
  )
}

function ActivityItem({ action, user, time, type }) {
  const icons = {
    info: <Clock className="text-blue-500" size={16} />,
    success: <CheckCircle className="text-green-500" size={16} />,
    warning: <AlertTriangle className="text-yellow-500" size={16} />,
  }
  
  return (
    <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
      {icons[type]}
      <div className="flex-1">
        <p className="text-sm font-medium text-gray-900">{action}</p>
        <p className="text-xs text-gray-600">{user} • {time}</p>
      </div>
    </div>
  )
}

function AlertItem({ severity, message, time }) {
  const colors = {
    warning: 'border-yellow-400 bg-yellow-50',
    error: 'border-red-400 bg-red-50',
    info: 'border-blue-400 bg-blue-50',
  }
  
  return (
    <div className={`p-4 border-l-4 ${colors[severity]} rounded`}>
      <p className="text-sm font-medium text-gray-900">{message}</p>
      <p className="text-xs text-gray-600 mt-1">{time}</p>
    </div>
  )
}
