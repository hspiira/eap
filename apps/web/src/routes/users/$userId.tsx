/**
 * User Detail Page
 * Displays user information and lifecycle actions
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { StatusBadge } from '@/components/common/StatusBadge'
import { LifecycleActions } from '@/components/common/LifecycleActions'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorDisplay } from '@/components/common/ErrorDisplay'
import { useToast } from '@/contexts/ToastContext'
import { usersApi } from '@/api/endpoints/users'
import type { User } from '@/types/entities'
import type { UserStatus } from '@/types/enums'
import { Edit, Mail, Shield, Calendar, Globe, Clock } from 'lucide-react'

export const Route = createFileRoute('/users/$userId')({
  component: UserDetailPage,
})

function UserDetailPage() {
  const { userId } = Route.useParams()
  const navigate = useNavigate()
  const { showSuccess, showError } = useToast()
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchUser = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await usersApi.getById(userId)
      setUser(data)
    } catch (err: any) {
      setError(err.message || 'Failed to load user')
      showError('Failed to load user')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchUser()
  }, [userId])

  const handleAction = async (action: string) => {
    try {
      setActionLoading(true)
      // TODO: Implement actual API calls for lifecycle actions
      // For now, just show a message
      showSuccess(`User ${action} action initiated`)
      // Refresh user data
      await fetchUser()
    } catch (err: any) {
      showError(`Failed to ${action} user`)
    } finally {
      setActionLoading(false)
    }
  }

  if (loading) {
    return (
      <AppLayout>
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center p-12">
            <LoadingSpinner size="lg" />
          </div>
        </div>
      </AppLayout>
    )
  }

  if (error || !user) {
    return (
      <AppLayout>
        <div className="max-w-7xl mx-auto">
          <ErrorDisplay
            error={error || 'User not found'}
            onRetry={fetchUser}
          />
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-text mb-2">{user.email}</h1>
            <div className="flex items-center gap-4">
              <StatusBadge status={user.status as UserStatus} />
              {user.is_email_verified && (
                <span className="text-sm text-primary flex items-center gap-1">
                  <Mail size={14} />
                  Email Verified
                </span>
              )}
              {user.is_two_factor_enabled && (
                <span className="text-sm text-primary flex items-center gap-1">
                  <Shield size={14} />
                  2FA Enabled
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-3">
            <LifecycleActions
              currentStatus={user.status}
              onAction={handleAction}
              loading={actionLoading}
            />
            <button
              onClick={() => navigate({ to: `/users/${userId}/edit` })}
              className="flex items-center gap-2 px-4 py-2 bg-neutral hover:bg-neutral-dark text-white rounded-none transition-colors"
            >
              <Edit size={18} />
              <span>Edit</span>
            </button>
          </div>
        </div>

        {/* User Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* Account Information */}
          <div className="bg-surface border border-[0.5px] border-border p-6">
            <h2 className="text-lg font-semibold text-text mb-4 flex items-center gap-2">
              <Mail size={20} />
              Account Information
            </h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-text-muted">Email</dt>
                <dd className="text-text mt-1">{user.email}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-text-muted">Status</dt>
                <dd className="text-text mt-1">
                  <StatusBadge status={user.status as UserStatus} size="sm" />
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-text-muted">Email Verified</dt>
                <dd className="text-text mt-1">
                  {user.is_email_verified ? (
                    <span className="text-primary">Yes</span>
                  ) : (
                    <span className="text-text-muted">No</span>
                  )}
                  {user.email_verified_at && (
                    <span className="text-xs text-text-muted ml-2">
                      ({new Date(user.email_verified_at).toLocaleDateString()})
                    </span>
                  )}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-text-muted">Two-Factor Authentication</dt>
                <dd className="text-text mt-1">
                  {user.is_two_factor_enabled ? (
                    <span className="text-primary">Enabled</span>
                  ) : (
                    <span className="text-text-muted">Disabled</span>
                  )}
                </dd>
              </div>
            </dl>
          </div>

          {/* Preferences */}
          <div className="bg-surface border border-[0.5px] border-border p-6">
            <h2 className="text-lg font-semibold text-text mb-4 flex items-center gap-2">
              <Globe size={20} />
              Preferences
            </h2>
            <dl className="space-y-3">
              {user.preferred_language && (
                <div>
                  <dt className="text-sm font-medium text-text-muted">Preferred Language</dt>
                  <dd className="text-text mt-1">{user.preferred_language}</dd>
                </div>
              )}
              {user.timezone && (
                <div>
                  <dt className="text-sm font-medium text-text-muted">Timezone</dt>
                  <dd className="text-text mt-1">{user.timezone}</dd>
                </div>
              )}
            </dl>
          </div>

          {/* Activity */}
          <div className="bg-surface border border-[0.5px] border-border p-6">
            <h2 className="text-lg font-semibold text-text mb-4 flex items-center gap-2">
              <Clock size={20} />
              Activity
            </h2>
            <dl className="space-y-3">
              {user.last_login_at && (
                <div>
                  <dt className="text-sm font-medium text-text-muted">Last Login</dt>
                  <dd className="text-text mt-1">
                    {new Date(user.last_login_at).toLocaleString()}
                  </dd>
                </div>
              )}
              {user.status_changed_at && (
                <div>
                  <dt className="text-sm font-medium text-text-muted">Status Changed</dt>
                  <dd className="text-text mt-1">
                    {new Date(user.status_changed_at).toLocaleString()}
                  </dd>
                </div>
              )}
            </dl>
          </div>

          {/* Metadata */}
          <div className="bg-surface border border-[0.5px] border-border p-6">
            <h2 className="text-lg font-semibold text-text mb-4 flex items-center gap-2">
              <Calendar size={20} />
              Metadata
            </h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-text-muted">Created</dt>
                <dd className="text-text mt-1">
                  {new Date(user.created_at).toLocaleString()}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-text-muted">Last Updated</dt>
                <dd className="text-text mt-1">
                  {new Date(user.updated_at).toLocaleString()}
                </dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </AppLayout>
  )
}
