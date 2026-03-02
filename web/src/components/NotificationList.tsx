/**
 * Notification list component — shows user notifications.
 */

import React, { useState, useEffect } from 'react'
import { relativeTime } from '../utils/dates'

interface Notification {
  id: string
  user_id: string
  type: string
  subject: string
  body: string
  sent_at: string
  read: boolean
  metadata: Record<string, unknown>
}

function NotificationList() {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [loading, setLoading] = useState(true)
  const [showUnreadOnly, setShowUnreadOnly] = useState(false)

  useEffect(() => {
    fetchNotifications()
  }, [showUnreadOnly])

  async function fetchNotifications() {
    setLoading(true)
    try {
      const response = await fetch(
        `/api/notifications/user/user_001?unread_only=${showUnreadOnly}`
      )
      if (!response.ok) throw new Error('Failed to fetch notifications')
      const data = await response.json()
      setNotifications(data.notifications)
    } catch (err) {
      console.error('Failed to fetch notifications:', err)
    } finally {
      setLoading(false)
    }
  }

  async function markAsRead(notificationId: string) {
    try {
      await fetch(`/api/notifications/read/${notificationId}`, { method: 'PUT' })
      setNotifications((prev) =>
        prev.map((n) => (n.id === notificationId ? { ...n, read: true } : n))
      )
    } catch (err) {
      console.error('Failed to mark notification as read:', err)
    }
  }

  const unreadCount = notifications.filter((n) => !n.read).length

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="card-title">
          Notifications
          {unreadCount > 0 && (
            <span
              style={{
                marginLeft: '0.5rem',
                background: 'var(--danger)',
                color: 'white',
                borderRadius: '12px',
                padding: '0.125rem 0.5rem',
                fontSize: '0.75rem',
              }}
            >
              {unreadCount}
            </span>
          )}
        </h2>
        <label style={{ fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
          <input
            type="checkbox"
            checked={showUnreadOnly}
            onChange={(e) => setShowUnreadOnly(e.target.checked)}
          />
          Unread only
        </label>
      </div>

      {loading ? (
        <div className="loading">Loading notifications...</div>
      ) : notifications.length === 0 ? (
        <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem' }}>
          No notifications
        </div>
      ) : (
        <div>
          {notifications.map((notification) => (
            <div
              key={notification.id}
              style={{
                padding: '1rem',
                borderBottom: '1px solid var(--border)',
                background: notification.read ? 'transparent' : '#f0f9ff',
                cursor: notification.read ? 'default' : 'pointer',
              }}
              onClick={() => !notification.read && markAsRead(notification.id)}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  {!notification.read && (
                    <div
                      style={{
                        width: '8px',
                        height: '8px',
                        borderRadius: '50%',
                        background: 'var(--primary-light)',
                      }}
                    />
                  )}
                  <strong style={{ fontSize: '0.875rem' }}>{notification.subject}</strong>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span
                    style={{
                      fontSize: '0.625rem',
                      padding: '0.125rem 0.375rem',
                      borderRadius: '4px',
                      background: notification.type === 'email' ? '#e2e8f0' : '#fefcbf',
                      textTransform: 'uppercase',
                      fontWeight: 600,
                    }}
                  >
                    {notification.type}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {relativeTime(notification.sent_at)}
                  </span>
                </div>
              </div>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                {notification.body}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default NotificationList
