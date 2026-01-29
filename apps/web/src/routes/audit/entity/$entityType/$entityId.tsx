/**
 * Entity Audit History Page
 * Timeline of changes for a specific entity
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorDisplay } from '@/components/common/ErrorDisplay'
import { auditApi } from '@/api/endpoints/audit'
import { usersApi } from '@/api/endpoints/users'
import type { AuditLog } from '@/types/entities'
import { ArrowLeft, Shield, FileText, User, Calendar } from 'lucide-react'

export const Route = createFileRoute('/audit/entity/$entityType/$entityId')({
  component: EntityHistoryPage,
})

function EntityHistoryPage() {
  const { entityType, entityId } = Route.useParams()
  const navigate = useNavigate()
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [users, setUsers] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchHistory = async () => {
    try {
      setLoading(true)
      setError(null)
      const history = await auditApi.getEntityHistory(entityType, entityId)
      setLogs(history)

      const userIds = [...new Set(history.map((l) => l.user_id).filter(Boolean))] as string[]
      const emailMap: Record<string, string> = {}
      await Promise.all(
        userIds.map(async (id) => {
          try {
            const u = await usersApi.getById(id)
            emailMap[id] = u.email
          } catch {
            emailMap[id] = id
          }
        })
      )
      setUsers(emailMap)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load entity history'
      setError(msg)
      console.error('Error fetching entity history:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchHistory()
  }, [entityType, entityId])

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

  if (error) {
    return (
      <AppLayout>
        <div className="max-w-7xl mx-auto">
          <ErrorDisplay error={error} onRetry={fetchHistory} />
        </div>
      </AppLayout>
    )
  }

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
            <h1 className="text-3xl font-bold text-safe flex items-center gap-2">
              <FileText size={28} />
              {entityType} History
            </h1>
            <p className="text-safe-light mt-1 font-mono text-sm">{entityId}</p>
          </div>
        </div>

        <div className="bg-white border border-[0.5px] border-safe/30 p-6">
          <h2 className="text-lg font-semibold text-safe mb-4">Timeline</h2>
          {logs.length === 0 ? (
            <p className="text-safe-light text-sm">No audit history for this entity.</p>
          ) : (
            <ul className="space-y-4">
              {[...logs]
                .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
                .map((log) => (
                  <li
                    key={log.id}
                    className="flex gap-4 py-3 px-4 rounded-none border-l-2 border-natural bg-safe-light/5 hover:bg-safe-light/10"
                  >
                    <div className="flex-shrink-0 text-safe-light text-sm flex items-center gap-1">
                      <Calendar size={14} />
                      {new Date(log.created_at).toLocaleString()}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-medium text-safe">{log.action_type}</span>
                        <span className="text-safe-light text-sm">·</span>
                        <span className="text-safe-light text-sm flex items-center gap-1">
                          <User size={14} />
                          {users[log.user_id ?? ''] ?? log.user_id ?? '—'}
                        </span>
                      </div>
                      <button
                        onClick={() => navigate({ to: `/audit/${log.id}` })}
                        className="mt-1 text-natural hover:text-natural-dark text-sm"
                      >
                        View details →
                      </button>
                    </div>
                  </li>
                ))}
            </ul>
          )}
        </div>
      </div>
    </AppLayout>
  )
}
