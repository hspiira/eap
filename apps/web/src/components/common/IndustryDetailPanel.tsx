/**
 * Industry Detail Panel
 * Displays industry details and children in a side panel (no navigation).
 */

import { Folder, Building2 } from 'lucide-react'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import type { Industry } from '@/types/entities'

export interface IndustryDetailPanelProps {
  industry: Industry | null
  children: Industry[]
  loading: boolean
  error: string | null
  onSelectParent: (id: string) => void
  onSelectChild: (id: string) => void
  onRetry: () => void
}

export function IndustryDetailPanel({
  industry,
  children,
  loading,
  error,
  onSelectParent,
  onSelectChild,
  onRetry,
}: IndustryDetailPanelProps) {
  if (loading) {
    return (
      <div className="flex flex-col h-full min-h-[240px] border border-[0.5px] border-border bg-surface p-6">
        <div className="flex items-center justify-center flex-1">
          <LoadingSpinner size="lg" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col h-full min-h-[240px] border border-[0.5px] border-border bg-surface p-6">
        <p className="text-danger font-medium mb-2">Error loading industry</p>
        <p className="text-text-muted text-sm mb-4">{error}</p>
        <button
          onClick={onRetry}
          className="self-start px-4 py-2 bg-primary hover:bg-primary-hover text-white text-sm rounded-none"
        >
          Retry
        </button>
      </div>
    )
  }

  if (!industry) {
    return (
      <div className="flex flex-col h-full min-h-[240px] border border-[0.5px] border-border bg-surface p-6">
        <p className="text-text-muted text-sm">Select an industry to view details.</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full min-h-0 border border-[0.5px] border-border bg-surface overflow-auto">
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-surface border border-[0.5px] border-border">
            <Folder size={22} className="text-primary" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-text">{industry.name}</h2>
            {industry.code && (
              <p className="text-text-muted text-sm">Code: {industry.code}</p>
            )}
            {industry.level != null && (
              <p className="text-text-muted text-xs">Level {industry.level}</p>
            )}
          </div>
        </div>
      </div>

      <div className="p-4 space-y-4 flex-1 overflow-auto">
        <section>
          <h3 className="text-sm font-semibold text-text mb-3">Details</h3>
          <dl className="space-y-2 text-sm">
            <div>
              <dt className="text-text-muted">Name</dt>
              <dd className="text-text">{industry.name}</dd>
            </div>
            {industry.code && (
              <div>
                <dt className="text-text-muted">Code</dt>
                <dd className="text-text">{industry.code}</dd>
              </div>
            )}
            {industry.parent_id && (
              <div>
                <dt className="text-text-muted">Parent</dt>
                <dd>
                  <button
                    type="button"
                    onClick={() => onSelectParent(industry.parent_id!)}
                    className="text-primary hover:text-primary-dark flex items-center gap-1"
                  >
                    <Building2 size={14} />
                    View parent industry
                  </button>
                </dd>
              </div>
            )}
            {industry.level != null && (
              <div>
                <dt className="text-text-muted">Level</dt>
                <dd className="text-text">{industry.level}</dd>
              </div>
            )}
            <div>
              <dt className="text-text-muted">Created</dt>
              <dd className="text-text">{new Date(industry.created_at).toLocaleString()}</dd>
            </div>
            <div>
              <dt className="text-text-muted">Updated</dt>
              <dd className="text-text">{new Date(industry.updated_at).toLocaleString()}</dd>
            </div>
          </dl>
        </section>

        <section>
          <h3 className="text-sm font-semibold text-text mb-3">Child Industries</h3>
          {children.length === 0 ? (
            <p className="text-text-muted text-sm">No child industries</p>
          ) : (
            <div className="space-y-1">
              {children.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  onClick={() => onSelectChild(c.id)}
                  className="flex items-center gap-2 w-full text-left py-2 px-3 rounded-none hover:bg-surface-hover transition-colors text-sm"
                >
                  <Folder size={14} className="text-text-muted flex-shrink-0" />
                  <span className="font-medium truncate">{c.name}</span>
                  {c.code && (
                    <span className="text-text-muted truncate">({c.code})</span>
                  )}
                </button>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
