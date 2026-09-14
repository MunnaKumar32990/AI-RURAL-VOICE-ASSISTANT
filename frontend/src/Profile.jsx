import React, { useState, useEffect } from 'react'
import { ArrowLeft, Edit2, Save, X, User, Mail, MapPin, Globe, Calendar, MessageSquare, TrendingUp, Activity, Award, Menu } from 'lucide-react'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function Profile({ user, onBack, onUserUpdate }) {
  const [isEditing, setIsEditing] = useState(false)
  const [editData, setEditData] = useState({
    email: user?.email || '',
    language: user?.language || 'en',
    location: user?.location || ''
  })
  const [queries, setQueries] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [stats, setStats] = useState({ total: 0, thisWeek: 0, types: {} })
  const [showMobileMenu, setShowMobileMenu] = useState(false)
  const [activeSection, setActiveSection] = useState('profile')

  useEffect(() => {
    fetchUserQueries()
  }, [])

  const fetchUserQueries = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await axios.get(`${API_URL}/api/user-queries`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      const queriesData = response.data.queries || []
      setQueries(queriesData)
      calculateStats(queriesData)
    } catch (err) {
      console.error('Failed to fetch queries:', err)
    }
  }

  const calculateStats = (queriesData) => {
    const now = new Date()
    const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
    const thisWeek = queriesData.filter(q => new Date(q.timestamp) > weekAgo).length
    const types = queriesData.reduce((acc, q) => {
      acc[q.type] = (acc[q.type] || 0) + 1
      return acc
    }, {})
    setStats({ total: queriesData.length, thisWeek, types })
  }

  const handleSave = async () => {
    setLoading(true)
    setError('')
    try {
      const token = localStorage.getItem('token')
      await axios.put(`${API_URL}/api/profile`, editData, {
        headers: { Authorization: `Bearer ${token}` }
      })
      onUserUpdate(editData)
      setIsEditing(false)
    } catch (err) {
      setError('Failed to update profile')
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = () => {
    setEditData({
      email: user?.email || '',
      language: user?.language || 'en',
      location: user?.location || ''
    })
    setIsEditing(false)
    setError('')
  }

  const getTypeIcon = (type) => {
    switch(type) {
      case 'voice': return '🎤'
      case 'text': return '✍️'
      case 'weather': return '🌤️'
      case 'crop': return '🌾'
      case 'schemes': return '🏛️'
      default: return '💬'
    }
  }

  const getTypeColor = (type) => {
    switch(type) {
      case 'voice': return '#8b5cf6'
      case 'text': return '#06b6d4'
      case 'weather': return '#f59e0b'
      case 'crop': return '#10b981'
      case 'schemes': return '#ef4444'
      default: return '#6b7280'
    }
  }

  return (
    <div className="profile-container">
      <div className="profile-hero">
        <div className="hero-background"></div>
        <div className="hero-content">
          <button onClick={onBack} className="back-button">
            <ArrowLeft size={20} />
            Back to Dashboard
          </button>
          <div className="profile-avatar">
            <div className="avatar-circle">
              <User size={40} />
            </div>
            <div className="avatar-status"></div>
          </div>
          <h1 className="profile-title">Welcome back!</h1>
          <p className="profile-subtitle">{user?.email}</p>
        </div>
      </div>

      <div className="profile-content">
        <div className="mobile-menu-toggle">
          <button onClick={() => setShowMobileMenu(!showMobileMenu)} className="menu-button">
            <Menu size={24} />
            Menu
          </button>
        </div>
        
        <div className={`mobile-menu ${showMobileMenu ? 'show' : ''}`}>
          <button 
            className={`menu-item ${activeSection === 'profile' ? 'active' : ''}`}
            onClick={() => { setActiveSection('profile'); setShowMobileMenu(false); }}
          >
            <User size={20} />
            Profile
          </button>
          <button 
            className={`menu-item ${activeSection === 'stats' ? 'active' : ''}`}
            onClick={() => { setActiveSection('stats'); setShowMobileMenu(false); }}
          >
            <TrendingUp size={20} />
            Activity Stats
          </button>
          <button 
            className={`menu-item ${activeSection === 'types' ? 'active' : ''}`}
            onClick={() => { setActiveSection('types'); setShowMobileMenu(false); }}
          >
            <Award size={20} />
            Query Types
          </button>
          <button 
            className={`menu-item ${activeSection === 'history' ? 'active' : ''}`}
            onClick={() => { setActiveSection('history'); setShowMobileMenu(false); }}
          >
            <MessageSquare size={20} />
            Query History
          </button>
        </div>
        
        <div className="profile-grid">
          <div className="profile-main">
            {(activeSection === 'profile' || window.innerWidth > 768) && (
            <div className="profile-card glass-card">
              <div className="card-header">
                <div className="header-icon">
                  <User size={24} />
                </div>
                <div className="header-content">
                  <h3>Profile Information</h3>
                  <p>Manage your personal details</p>
                </div>
                {!isEditing ? (
                  <button onClick={() => setIsEditing(true)} className="edit-button">
                    <Edit2 size={16} />
                    Edit
                  </button>
                ) : (
                  <div className="edit-actions">
                    <button onClick={handleSave} disabled={loading} className="save-button">
                      <Save size={16} />
                      {loading ? 'Saving...' : 'Save'}
                    </button>
                    <button onClick={handleCancel} className="cancel-button">
                      <X size={16} />
                    </button>
                  </div>
                )}
              </div>

              {error && <div className="error-message">{error}</div>}

              <div className="profile-fields">
                <div className="field-group">
                  <div className="field-icon">
                    <Mail size={20} />
                  </div>
                  <div className="field-content">
                    <label>Email Address</label>
                    {isEditing ? (
                      <input
                        type="email"
                        value={editData.email}
                        onChange={(e) => setEditData({...editData, email: e.target.value})}
                        className="field-input"
                      />
                    ) : (
                      <div className="field-value">{user?.email}</div>
                    )}
                  </div>
                </div>

                <div className="field-group">
                  <div className="field-icon">
                    <Globe size={20} />
                  </div>
                  <div className="field-content">
                    <label>Preferred Language</label>
                    {isEditing ? (
                      <select
                        value={editData.language}
                        onChange={(e) => setEditData({...editData, language: e.target.value})}
                        className="field-select"
                      >
                        <option value="en">🇺🇸 English</option>
                        <option value="hi">🇮🇳 Hindi</option>
                        <option value="mr">🇮🇳 Marathi</option>
                        <option value="bn">🇮🇳 Bengali</option>
                        <option value="ta">🇮🇳 Tamil</option>
                        <option value="te">🇮🇳 Telugu</option>
                      </select>
                    ) : (
                      <div className="field-value">
                        {editData.language === 'en' && '🇺🇸 English'}
                        {editData.language === 'hi' && '🇮🇳 Hindi'}
                        {editData.language === 'mr' && '🇮🇳 Marathi'}
                        {editData.language === 'bn' && '🇮🇳 Bengali'}
                        {editData.language === 'ta' && '🇮🇳 Tamil'}
                        {editData.language === 'te' && '🇮🇳 Telugu'}
                      </div>
                    )}
                  </div>
                </div>

                <div className="field-group">
                  <div className="field-icon">
                    <MapPin size={20} />
                  </div>
                  <div className="field-content">
                    <label>Location</label>
                    {isEditing ? (
                      <input
                        type="text"
                        value={editData.location}
                        onChange={(e) => setEditData({...editData, location: e.target.value})}
                        placeholder="City, State"
                        className="field-input"
                      />
                    ) : (
                      <div className="field-value">📍 {user?.location}</div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            )}
            
            {(activeSection === 'history' || window.innerWidth > 768) && (
            <div className="activity-card glass-card">
              <div className="card-header">
                <div className="header-icon">
                  <MessageSquare size={24} />
                </div>
                <div className="header-content">
                  <h3>Query History</h3>
                  <p>Your recent interactions with Gram Vaani</p>
                </div>
              </div>

              {queries.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-icon">💬</div>
                  <h4>No queries yet</h4>
                  <p>Start asking questions to see your history here!</p>
                </div>
              ) : (
                <div className="queries-timeline">
                  {queries.slice(0, 10).map((query, index) => (
                    <div key={index} className="timeline-item">
                      <div className="timeline-marker" style={{backgroundColor: getTypeColor(query.type)}}>
                        <span>{getTypeIcon(query.type)}</span>
                      </div>
                      <div className="timeline-content">
                        <div className="timeline-header">
                          <span className="query-type-badge" style={{backgroundColor: getTypeColor(query.type)}}>
                            {query.type}
                          </span>
                          <span className="query-time">
                            {new Date(query.timestamp).toLocaleDateString('en-US', {
                              month: 'short',
                              day: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </span>
                        </div>
                        <div className="query-text">{query.query}</div>
                        {query.response && (
                          <div className="query-response">
                            {query.response.length > 120 ? 
                              `${query.response.substring(0, 120)}...` : 
                              query.response
                            }
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            )}
          </div>

          <div className="profile-sidebar">
            {(activeSection === 'stats' || window.innerWidth > 768) && (
            <div className="stats-card glass-card">
              <div className="card-header">
                <div className="header-icon">
                  <TrendingUp size={24} />
                </div>
                <div className="header-content">
                  <h3>Activity Stats</h3>
                  <p>Your usage overview</p>
                </div>
              </div>
              <div className="stats-grid">
                <div className="stat-item">
                  <div className="stat-icon">
                    <Activity size={20} />
                  </div>
                  <div className="stat-content">
                    <div className="stat-number">{stats.total}</div>
                    <div className="stat-label">Total Queries</div>
                  </div>
                </div>
                <div className="stat-item">
                  <div className="stat-icon">
                    <Calendar size={20} />
                  </div>
                  <div className="stat-content">
                    <div className="stat-number">{stats.thisWeek}</div>
                    <div className="stat-label">This Week</div>
                  </div>
                </div>
              </div>
            </div>
            )}

            {(activeSection === 'types' || window.innerWidth > 768) && (
            <div className="types-card glass-card">
              <div className="card-header">
                <div className="header-icon">
                  <Award size={24} />
                </div>
                <div className="header-content">
                  <h3>Query Types</h3>
                  <p>What you ask about most</p>
                </div>
              </div>
              <div className="types-list">
                {Object.entries(stats.types).map(([type, count]) => (
                  <div key={type} className="type-item">
                    <div className="type-icon" style={{backgroundColor: getTypeColor(type)}}>
                      {getTypeIcon(type)}
                    </div>
                    <div className="type-content">
                      <div className="type-name">{type}</div>
                      <div className="type-count">{count} queries</div>
                    </div>
                    <div className="type-bar">
                      <div 
                        className="type-progress" 
                        style={{
                          width: `${(count / stats.total) * 100}%`,
                          backgroundColor: getTypeColor(type)
                        }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Profile