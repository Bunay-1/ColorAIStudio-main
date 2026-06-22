import React, { useState, useEffect } from 'react'
import { Save, Shield, Bell, Database, Key, Globe, Users } from 'lucide-react'

export default function Settings() {
  const [activeTab, setActiveTab] = useState('general')
  const [settings, setSettings] = useState({
    general: {
      siteName: 'ICAP Enterprise',
      timezone: 'UTC',
      language: 'en'
    },
    security: {
      sessionTimeout: 480,
      passwordMinLength: 8,
      requireMFA: false,
      maxLoginAttempts: 5
    },
    notifications: {
      emailAlerts: true,
      slackWebhook: '',
      alertThreshold: 'warning'
    },
    database: {
      backupEnabled: true,
      backupSchedule: 'daily',
      retentionDays: 30
    },
    api: {
      rateLimitEnabled: true,
      requestsPerMinute: 60,
      corsEnabled: true
    }
  })

  const [saveStatus, setSaveStatus] = useState('')

  const handleSave = async (section) => {
    setSaveStatus('saving')
    try {
      // In a real implementation, this would save to the API
      await new Promise(resolve => setTimeout(resolve, 1000))
      setSaveStatus('saved')
      setTimeout(() => setSaveStatus(''), 2000)
    } catch (error) {
      setSaveStatus('error')
    }
  }

  const tabs = [
    { id: 'general', label: 'General', icon: Globe },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'database', label: 'Database', icon: Database },
    { id: 'api', label: 'API', icon: Key },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-1">Configure system settings and preferences</p>
      </div>

      <div className="flex gap-6">
        {/* Sidebar */}
        <div className="w-64 space-y-2">
          {tabs.map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                  activeTab === tab.id
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <Icon size={20} />
                <span>{tab.label}</span>
              </button>
            )
          })}
        </div>

        {/* Content */}
        <div className="flex-1">
          {activeTab === 'general' && <GeneralSettings settings={settings.general} onSave={() => handleSave('general')} />}
          {activeTab === 'security' && <SecuritySettings settings={settings.security} onSave={() => handleSave('security')} />}
          {activeTab === 'notifications' && <NotificationSettings settings={settings.notifications} onSave={() => handleSave('notifications')} />}
          {activeTab === 'database' && <DatabaseSettings settings={settings.database} onSave={() => handleSave('database')} />}
          {activeTab === 'api' && <APISettings settings={settings.api} onSave={() => handleSave('api')} />}
        </div>
      </div>

      {saveStatus && (
        <div className={`fixed bottom-4 right-4 px-6 py-3 rounded-lg ${
          saveStatus === 'saved' ? 'bg-green-500 text-white' :
          saveStatus === 'saving' ? 'bg-blue-500 text-white' :
          'bg-red-500 text-white'
        }`}>
          {saveStatus === 'saved' ? 'Settings saved successfully' :
           saveStatus === 'saving' ? 'Saving...' :
           'Error saving settings'}
        </div>
      )}
    </div>
  )
}

function GeneralSettings({ settings, onSave }) {
  const [localSettings, setLocalSettings] = useState(settings)

  const handleChange = (key, value) => {
    setLocalSettings({ ...localSettings, [key]: value })
  }

  return (
    <div className="card space-y-6">
      <h2 className="text-xl font-semibold">General Settings</h2>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Site Name</label>
        <input
          type="text"
          value={localSettings.siteName}
          onChange={(e) => handleChange('siteName', e.target.value)}
          className="input-field"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Timezone</label>
        <select
          value={localSettings.timezone}
          onChange={(e) => handleChange('timezone', e.target.value)}
          className="input-field"
        >
          <option value="UTC">UTC</option>
          <option value="America/New_York">America/New_York</option>
          <option value="Europe/London">Europe/London</option>
          <option value="Asia/Tokyo">Asia/Tokyo</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Language</label>
        <select
          value={localSettings.language}
          onChange={(e) => handleChange('language', e.target.value)}
          className="input-field"
        >
          <option value="en">English</option>
          <option value="bg">Bulgarian</option>
          <option value="de">German</option>
          <option value="fr">French</option>
        </select>
      </div>

      <div className="flex justify-end">
        <button onClick={onSave} className="btn-primary flex items-center space-x-2">
          <Save size={20} />
          <span>Save Changes</span>
        </button>
      </div>
    </div>
  )
}

function SecuritySettings({ settings, onSave }) {
  const [localSettings, setLocalSettings] = useState(settings)

  const handleChange = (key, value) => {
    setLocalSettings({ ...localSettings, [key]: value })
  }

  return (
    <div className="card space-y-6">
      <h2 className="text-xl font-semibold">Security Settings</h2>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Session Timeout (minutes)</label>
        <input
          type="number"
          value={localSettings.sessionTimeout}
          onChange={(e) => handleChange('sessionTimeout', parseInt(e.target.value))}
          className="input-field"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Minimum Password Length</label>
        <input
          type="number"
          value={localSettings.passwordMinLength}
          onChange={(e) => handleChange('passwordMinLength', parseInt(e.target.value))}
          className="input-field"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Maximum Login Attempts</label>
        <input
          type="number"
          value={localSettings.maxLoginAttempts}
          onChange={(e) => handleChange('maxLoginAttempts', parseInt(e.target.value))}
          className="input-field"
        />
      </div>

      <div className="flex items-center space-x-3">
        <input
          type="checkbox"
          id="mfa"
          checked={localSettings.requireMFA}
          onChange={(e) => handleChange('requireMFA', e.target.checked)}
          className="w-4 h-4"
        />
        <label htmlFor="mfa" className="text-sm font-medium text-gray-700">
          Require Multi-Factor Authentication
        </label>
      </div>

      <div className="flex justify-end">
        <button onClick={onSave} className="btn-primary flex items-center space-x-2">
          <Save size={20} />
          <span>Save Changes</span>
        </button>
      </div>
    </div>
  )
}

function NotificationSettings({ settings, onSave }) {
  const [localSettings, setLocalSettings] = useState(settings)

  const handleChange = (key, value) => {
    setLocalSettings({ ...localSettings, [key]: value })
  }

  return (
    <div className="card space-y-6">
      <h2 className="text-xl font-semibold">Notification Settings</h2>
      
      <div className="flex items-center space-x-3">
        <input
          type="checkbox"
          id="emailAlerts"
          checked={localSettings.emailAlerts}
          onChange={(e) => handleChange('emailAlerts', e.target.checked)}
          className="w-4 h-4"
        />
        <label htmlFor="emailAlerts" className="text-sm font-medium text-gray-700">
          Enable Email Alerts
        </label>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Slack Webhook URL</label>
        <input
          type="url"
          value={localSettings.slackWebhook}
          onChange={(e) => handleChange('slackWebhook', e.target.value)}
          className="input-field"
          placeholder="https://hooks.slack.com/services/..."
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Alert Threshold</label>
        <select
          value={localSettings.alertThreshold}
          onChange={(e) => handleChange('alertThreshold', e.target.value)}
          className="input-field"
        >
          <option value="info">Info</option>
          <option value="warning">Warning</option>
          <option value="error">Error</option>
          <option value="critical">Critical</option>
        </select>
      </div>

      <div className="flex justify-end">
        <button onClick={onSave} className="btn-primary flex items-center space-x-2">
          <Save size={20} />
          <span>Save Changes</span>
        </button>
      </div>
    </div>
  )
}

function DatabaseSettings({ settings, onSave }) {
  const [localSettings, setLocalSettings] = useState(settings)

  const handleChange = (key, value) => {
    setLocalSettings({ ...localSettings, [key]: value })
  }

  return (
    <div className="card space-y-6">
      <h2 className="text-xl font-semibold">Database Settings</h2>
      
      <div className="flex items-center space-x-3">
        <input
          type="checkbox"
          id="backupEnabled"
          checked={localSettings.backupEnabled}
          onChange={(e) => handleChange('backupEnabled', e.target.checked)}
          className="w-4 h-4"
        />
        <label htmlFor="backupEnabled" className="text-sm font-medium text-gray-700">
          Enable Automated Backups
        </label>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Backup Schedule</label>
        <select
          value={localSettings.backupSchedule}
          onChange={(e) => handleChange('backupSchedule', e.target.value)}
          className="input-field"
        >
          <option value="hourly">Hourly</option>
          <option value="daily">Daily</option>
          <option value="weekly">Weekly</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Retention Period (days)</label>
        <input
          type="number"
          value={localSettings.retentionDays}
          onChange={(e) => handleChange('retentionDays', parseInt(e.target.value))}
          className="input-field"
        />
      </div>

      <div className="flex justify-end">
        <button onClick={onSave} className="btn-primary flex items-center space-x-2">
          <Save size={20} />
          <span>Save Changes</span>
        </button>
      </div>
    </div>
  )
}

function APISettings({ settings, onSave }) {
  const [localSettings, setLocalSettings] = useState(settings)

  const handleChange = (key, value) => {
    setLocalSettings({ ...localSettings, [key]: value })
  }

  return (
    <div className="card space-y-6">
      <h2 className="text-xl font-semibold">API Settings</h2>
      
      <div className="flex items-center space-x-3">
        <input
          type="checkbox"
          id="rateLimitEnabled"
          checked={localSettings.rateLimitEnabled}
          onChange={(e) => handleChange('rateLimitEnabled', e.target.checked)}
          className="w-4 h-4"
        />
        <label htmlFor="rateLimitEnabled" className="text-sm font-medium text-gray-700">
          Enable Rate Limiting
        </label>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Requests Per Minute</label>
        <input
          type="number"
          value={localSettings.requestsPerMinute}
          onChange={(e) => handleChange('requestsPerMinute', parseInt(e.target.value))}
          className="input-field"
        />
      </div>

      <div className="flex items-center space-x-3">
        <input
          type="checkbox"
          id="corsEnabled"
          checked={localSettings.corsEnabled}
          onChange={(e) => handleChange('corsEnabled', e.target.checked)}
          className="w-4 h-4"
        />
        <label htmlFor="corsEnabled" className="text-sm font-medium text-gray-700">
          Enable CORS
        </label>
      </div>

      <div className="flex justify-end">
        <button onClick={onSave} className="btn-primary flex items-center space-x-2">
          <Save size={20} />
          <span>Save Changes</span>
        </button>
      </div>
    </div>
  )
}
