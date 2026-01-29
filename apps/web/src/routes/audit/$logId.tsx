/**
 * Audit Log Detail Page
 * Log details, entity changes, user info, timestamp
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorDisplay } from '@/components/common/ErrorDisplay'
import { auditApi, type AuditLogChange } from '@/api/endpoints/audit'
import { usersApi } from '@/api/endpoints/users'
import type { AuditLog } from '@/types/entities'
import { ArrowLeft, Shield, Calendar, User, FileText, Globe, Monitor } from 'lucide-react'

export const Route = createFileRoute('/audit/$logId')({
  component: AuditLogDetailPage,
})

function AuditLogDetailPage() {
  const { logId } = Route.useParams()
  const navigate = useNavigate()
  const [log, setLog] = useState<AuditLog | null>(null)
  const [changes, setChanges] = useState<AuditLogChange[] | Record<string, unknown> | null>(null)
  const [userEmail, setUserEmail] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchLog = async () => {
    try {
      setLoading(true)
      setError(null)
      const [logData, changesData] = await Promise.all([
        auditApi.getById(logId),
        auditApi.getChanges(logId).catch(() => null),
      ])
      setLog(logData)
      setChanges(changesData)

      if (logData.user_id) {
        try {
          const u = await usersApi.getById(logData.user_id)
          setUserEmail(u.email)
        } catch {
          setUserEmail(null)
        }
      } else {
        setUserEmail(null)
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load audit log'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLog()
  }, [logId])

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

  if (error || !log) {
    return (
      <AppLayout>
        <div className="max-w-7xl mx-auto">
          <ErrorDisplay error={error ?? 'Audit log not found'} onRetry={fetchLog} />
        </div>
      </AppLayout>
    )
  }

  const changeList = Array.isArray(changes) ? changes : null
  const changeObj = changes && !Array.isArray(changes) && typeof changes === 'object' ? (changes as Record<string, unknown>) : null

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        <button
          onClick={() => navigate({ to: '/audit' })}
          className="flex items-center gap-2 text-safe hover:text-natural mb-6 transition-colors"
        >
          <ArrowLeft size={18} />
          <span>Back to Audit Logs</span>
        </button>

        <div className="flex items-center gap-4 mb-6">
          <div className="p-3 bg-white border border-[0.5px] border-safe/30">
            <Shield size={28} className="text-natural" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-safe">
              {log.action_type} · {log.resource_type}
            </h1>
            <p className="text-safe-light mt-1">
              {new Date(log.created_at).toLocaleString()}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white border border-[0.5px] border-safe/30 p-6">
            <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
              <FileText size={20} />
              Details
            </h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-safe-light">Action</dt>
                <dd className="text-safe mt-1 font-medium">{log.action_type}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-safe-light">Resource</dt>
                <dd className="text-safe mt-1">{log.resource_type}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-safe-light">Resource ID</dt>
                <dd className="text-safe mt-1">
                  <button
                    onClick={() => navigate({ to: `/audit/entity/${log.resource_type}/${log.resource_id}` })}
                    className="text-natural hover:text-natural-dark font-mono text-sm"
                  >
                    {log.resource_id}
                  </button>
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-safe-light flex items-center gap-1">
                  <User size={14} />
                  User
                </dt>
                <dd className="text-safe mt-1">
                  {userEmail ?? log.user_id ?? '—'}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-safe-light flex items-center gap-1">
                  <Calendar size={14} />
                  Timestamp
                </dt>
                <dd className="text-safe mt-1">{new Date(log.created_at).toLocaleString()}</dd>
              </div>
              {log.ip_address && (
                <div>
                  <dt className="text-sm font-medium text-safe-light flex items-center gap-1">
                    <Globe size={14} />
                    IP Address
                  </dt>
                  <dd className="text-safe mt-1 font-mono text-sm">{log.ip_address}</dd>
                </div>
              )}
              {log.user_agent && (
                <div>
                  <dt className="text-sm font-medium text-safe-light flex items-center gap-1">
                    <Monitor size={14} />
                    User Agent
                  </dt>
                  <dd className="text-safe mt-1 text-sm break-all">{log.user_agent}</dd>
                </div>
              )}
            </dl>
          </div>

          <div className="bg-white border border-[0.5px] border-safe/30 p-6">
            <h2 className="text-lg font-semibold text-safe mb-4">Entity Changes</h2>
            {changeList && changeList.length > 0 ? (
              <div className="space-y-3">
                {changeList.map((c, i) => (
                  <div
                    key={i}
                    className="py-2 px-3 rounded-none bg-safe-light/5 border border-[0.5px] border-safe/30"
                  >
                    {c.field && (
                      <p className="text-sm font-medium text-safe mb-1">{c.field}</p>
                    )}
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="text-safe-light">Old: </span>
                        <code className="text-nurturing break-all">
                          {c.old_value !== undefined && c.old_value !== null
                            ? JSON.stringify(c.old_value)
                            : '—'}
                        </code>
                      </div>
                      <div>
                        <span className="text-safe-light">New: </span>
                        <code className="text-natural break-all">
                          {c.new_value !== undefined && c.new_value !== null
                            ? JSON.stringify(c.new_value)
                            : '—'}
                        </code>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : changeObj && Object.keys(changeObj).length > 0 ? (
              <pre className="text-sm text-safe overflow-x-auto p-4 bg-safe-light/5 rounded-none border border-[0.5px] border-safe/30">
                {JSON.stringify(changeObj, null, 2)}
              </pre>
            ) : log.changes && typeof log.changes === 'object' && Object.keys(log.changes).length > 0 ? (
              <pre className="text-sm text-safe overflow-x-auto p-4 bg-safe-light/5 rounded-none border border-[0.5px] border-safe/30">
                {JSON.stringify(log.changes, null, 2)}
              </pre>
            ) : (
              <p className="text-safe-light text-sm">No change details available.</p>
            )}
          </div>
        </div>
      </div>
    </AppLayout>
  )
}
