/**
 * Industry Detail Page
 * Industry details and child industries
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorDisplay } from '@/components/common/ErrorDisplay'
import { useToast } from '@/contexts/ToastContext'
import { industriesApi } from '@/api/endpoints/industries'
import type { Industry } from '@/types/entities'
import { ArrowLeft, Folder, Building2 } from 'lucide-react'

export const Route = createFileRoute('/industries/$industryId')({
  component: IndustryDetailPage,
})

function IndustryDetailPage() {
  const { industryId } = Route.useParams()
  const navigate = useNavigate()
  const { showError } = useToast()
  const [industry, setIndustry] = useState<Industry | null>(null)
  const [children, setChildren] = useState<Industry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchIndustry = async () => {
    try {
      setLoading(true)
      setError(null)
      const [data, childList] = await Promise.all([
        industriesApi.getById(industryId),
        industriesApi.getChildren(industryId).catch(() => []),
      ])
      setIndustry(data)
      setChildren(childList)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load industry'
      setError(msg)
      showError('Failed to load industry')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchIndustry()
  }, [industryId])

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

  if (error || !industry) {
    return (
      <AppLayout>
        <div className="max-w-7xl mx-auto">
          <ErrorDisplay error={error ?? 'Industry not found'} onRetry={fetchIndustry} />
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        <button
          onClick={() => navigate({ to: '/industries' })}
          className="flex items-center gap-2 text-safe hover:text-natural mb-6 transition-colors"
        >
          <ArrowLeft size={18} />
          <span>Back to Industries</span>
        </button>

        <div className="flex items-center gap-4 mb-6">
          <div className="p-3 bg-calm border border-[0.5px] border-safe/30">
            <Folder size={28} className="text-natural" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-safe">{industry.name}</h1>
            {industry.code && (
              <p className="text-safe-light mt-1">Code: {industry.code}</p>
            )}
            {industry.level != null && (
              <p className="text-safe-light text-sm">Level {industry.level}</p>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-calm border border-[0.5px] border-safe/30 p-6">
            <h2 className="text-lg font-semibold text-safe mb-4">Details</h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-safe-light">Name</dt>
                <dd className="text-safe mt-1">{industry.name}</dd>
              </div>
              {industry.code && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">Code</dt>
                  <dd className="text-safe mt-1">{industry.code}</dd>
                </div>
              )}
              {industry.parent_id && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">Parent</dt>
                  <dd className="text-safe mt-1">
                    <button
                      onClick={() => navigate({ to: `/industries/${industry.parent_id}` })}
                      className="text-natural hover:text-natural-dark flex items-center gap-1"
                    >
                      <Building2 size={14} />
                      View parent industry
                    </button>
                  </dd>
                </div>
              )}
              {industry.level != null && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">Level</dt>
                  <dd className="text-safe mt-1">{industry.level}</dd>
                </div>
              )}
              <div>
                <dt className="text-sm font-medium text-safe-light">Created</dt>
                <dd className="text-safe mt-1">
                  {new Date(industry.created_at).toLocaleString()}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-safe-light">Updated</dt>
                <dd className="text-safe mt-1">
                  {new Date(industry.updated_at).toLocaleString()}
                </dd>
              </div>
            </dl>
          </div>

          <div className="bg-calm border border-[0.5px] border-safe/30 p-6">
            <h2 className="text-lg font-semibold text-safe mb-4">Child Industries</h2>
            {children.length === 0 ? (
              <p className="text-safe-light text-sm">No child industries</p>
            ) : (
              <div className="space-y-2">
                {children.map((c) => (
                  <button
                    key={c.id}
                    onClick={() => navigate({ to: `/industries/${c.id}` })}
                    className="flex items-center gap-2 w-full text-left py-2 px-3 rounded-none hover:bg-safe-light/10 transition-colors"
                  >
                    <Folder size={16} className="text-safe-light" />
                    <span className="font-medium">{c.name}</span>
                    {c.code && (
                      <span className="text-safe-light text-sm">({c.code})</span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </AppLayout>
  )
}
