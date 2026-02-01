/**
 * Client Tag Detail Page
 * Tag details and assigned clients list
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorDisplay } from '@/components/common/ErrorDisplay'
import { useToast } from '@/contexts/ToastContext'
import { clientTagsApi } from '@/api/endpoints/client-tags'
import type { ClientTag } from '@/types/entities'
import type { Client } from '@/types/entities'
import { ArrowLeft, Tag, UserCircle, Building2 } from 'lucide-react'

export const Route = createFileRoute('/client-tags/$tagId')({
  component: ClientTagDetailPage,
})

function ClientTagDetailPage() {
  const { tagId } = Route.useParams()
  const navigate = useNavigate()
  const { showError } = useToast()
  const [tag, setTag] = useState<ClientTag | null>(null)
  const [clients, setClients] = useState<Client[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [unassigningId, setUnassigningId] = useState<string | null>(null)

  const fetchTag = async () => {
    try {
      setLoading(true)
      setError(null)
      const [tagData, clientsData] = await Promise.all([
        clientTagsApi.getById(tagId),
        clientTagsApi.getAssignedClients(tagId).catch(() => []),
      ])
      setTag(tagData)
      setClients(clientsData)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load tag'
      setError(msg)
      showError('Failed to load tag')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTag()
  }, [tagId])

  const handleUnassign = async (clientId: string) => {
    try {
      setUnassigningId(clientId)
      await clientTagsApi.unassign(tagId, clientId)
      setClients((prev) => prev.filter((c) => c.id !== clientId))
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to remove tag from client'
      showError(msg)
    } finally {
      setUnassigningId(null)
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

  if (error || !tag) {
    return (
      <AppLayout>
        <div className="max-w-7xl mx-auto">
          <ErrorDisplay error={error ?? 'Tag not found'} onRetry={fetchTag} />
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        <button
          onClick={() => navigate({ to: '/client-tags' })}
          className="flex items-center gap-2 text-safe hover:text-natural mb-6 transition-colors"
        >
          <ArrowLeft size={18} />
          <span>Back to Tags</span>
        </button>

        <div className="flex items-center gap-4 mb-6">
          <div
            className="p-3 bg-white border border-[0.5px] border-safe/30 flex items-center justify-center"
            style={tag.color ? { backgroundColor: `${tag.color}20` } : undefined}
          >
            <Tag size={28} className="text-natural" style={tag.color ? { color: tag.color } : undefined} />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-safe">{tag.name}</h1>
            {tag.description && (
              <p className="text-safe-light mt-1 max-w-2xl">{tag.description}</p>
            )}
            {tag.color && (
              <p className="text-safe-light text-sm mt-1 flex items-center gap-2">
                <span
                  className="w-3 h-3 rounded-full border border-[0.5px] border-safe/30"
                  style={{ backgroundColor: tag.color }}
                />
                {tag.color}
              </p>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white border border-[0.5px] border-safe/30 p-6">
            <h2 className="text-lg font-semibold text-safe mb-4">Details</h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-safe-light">Name</dt>
                <dd className="text-safe mt-1">{tag.name}</dd>
              </div>
              {tag.color && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">Color</dt>
                  <dd className="text-safe mt-1 flex items-center gap-2">
                    <span
                      className="w-4 h-4 rounded-full border border-[0.5px] border-safe/30"
                      style={{ backgroundColor: tag.color }}
                    />
                    {tag.color}
                  </dd>
                </div>
              )}
              {tag.description && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">Description</dt>
                  <dd className="text-safe mt-1">{tag.description}</dd>
                </div>
              )}
              <div>
                <dt className="text-sm font-medium text-safe-light">Created</dt>
                <dd className="text-safe mt-1">{new Date(tag.created_at).toLocaleString()}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-safe-light">Updated</dt>
                <dd className="text-safe mt-1">{new Date(tag.updated_at).toLocaleString()}</dd>
              </div>
            </dl>
          </div>

          <div className="bg-white border border-[0.5px] border-safe/30 p-6">
            <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
              <UserCircle size={20} />
              Assigned Clients ({clients.length})
            </h2>
            {clients.length === 0 ? (
              <p className="text-safe-light text-sm">No clients assigned to this tag.</p>
            ) : (
              <ul className="space-y-2">
                {clients.map((c) => (
                  <li
                    key={c.id}
                    className="flex items-center justify-between py-2 px-3 rounded-none hover:bg-safe-light/5 group"
                  >
                    <button
                      onClick={() => navigate({ to: `/clients/${c.id}` })}
                      className="flex items-center gap-2 text-left text-natural hover:text-natural-dark font-medium"
                    >
                      <Building2 size={16} className="text-safe-light" />
                      {c.name}
                    </button>
                    <button
                      onClick={() => handleUnassign(c.id)}
                      disabled={unassigningId === c.id}
                      className="text-sm text-nurturing hover:text-nurturing-dark opacity-0 group-hover:opacity-100 transition-opacity disabled:opacity-50"
                    >
                      {unassigningId === c.id ? 'Removing…' : 'Remove'}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </AppLayout>
  )
}
