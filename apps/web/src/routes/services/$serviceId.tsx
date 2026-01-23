/**
 * Service Detail Page
 * Displays service information, group settings, and lifecycle actions
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { StatusBadge } from '@/components/common/StatusBadge'
import { LifecycleActions } from '@/components/common/LifecycleActions'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorDisplay } from '@/components/common/ErrorDisplay'
import { useToast } from '@/contexts/ToastContext'
import { servicesApi } from '@/api/endpoints/services'
import type { Service } from '@/types/entities'
import type { BaseStatus } from '@/types/enums'
import { Edit, Package, Clock, Users, Settings } from 'lucide-react'

export const Route = createFileRoute('/services/$serviceId')({
  component: ServiceDetailPage,
})

function ServiceDetailPage() {
  const { serviceId } = Route.useParams()
  const navigate = useNavigate()
  const { showSuccess, showError } = useToast()
  const [service, setService] = useState<Service | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchService = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await servicesApi.getById(serviceId)
      setService(data)
    } catch (err: any) {
      setError(err.message || 'Failed to load service')
      showError('Failed to load service')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchService()
  }, [serviceId])

  const handleAction = async (action: string) => {
    try {
      setActionLoading(true)
      let updatedService: Service

      switch (action) {
        case 'activate':
          updatedService = await servicesApi.activate(serviceId)
          break
        case 'deactivate':
          updatedService = await servicesApi.deactivate(serviceId)
          break
        case 'archive':
          updatedService = await servicesApi.archive(serviceId)
          break
        case 'restore':
          updatedService = await servicesApi.restore(serviceId)
          break
        default:
          throw new Error(`Unknown action: ${action}`)
      }

      setService(updatedService)
      showSuccess(`Service ${action}d successfully`)
    } catch (err: any) {
      showError(`Failed to ${action} service: ${err.message || 'Unknown error'}`)
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

  if (error || !service) {
    return (
      <AppLayout>
        <div className="max-w-7xl mx-auto">
          <ErrorDisplay
            error={error || 'Service not found'}
            onRetry={fetchService}
          />
        </div>
      </AppLayout>
    )
  }

  const formatDuration = (minutes: number | null | undefined) => {
    if (!minutes) return '-'
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    if (hours > 0) {
      return `${hours}h ${mins > 0 ? `${mins}m` : ''}`
    }
    return `${mins}m`
  }

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-safe mb-2">{service.name}</h1>
            <div className="flex items-center gap-4">
              <StatusBadge status={service.status as BaseStatus} />
            </div>
          </div>
          <div className="flex items-center gap-3">
            <LifecycleActions
              currentStatus={service.status}
              onAction={handleAction}
              loading={actionLoading}
            />
            <button
              onClick={() => navigate({ to: `/services/${serviceId}/edit` })}
              className="flex items-center gap-2 px-4 py-2 bg-safe hover:bg-safe-dark text-white rounded-none transition-colors"
            >
              <Edit size={18} />
              <span>Edit</span>
            </button>
          </div>
        </div>

        {/* Service Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* Service Details */}
          <div className="bg-calm border border-[0.5px] border-safe p-6">
            <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
              <Package size={20} />
              Service Details
            </h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-safe-light">Name</dt>
                <dd className="text-safe mt-1">{service.name}</dd>
              </div>
              {service.description && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">Description</dt>
                  <dd className="text-safe mt-1">{service.description}</dd>
                </div>
              )}
              <div>
                <dt className="text-sm font-medium text-safe-light">Status</dt>
                <dd className="text-safe mt-1">
                  <StatusBadge status={service.status as BaseStatus} size="sm" />
                </dd>
              </div>
              {service.service_type && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">Service Type</dt>
                  <dd className="text-safe mt-1">{service.service_type}</dd>
                </div>
              )}
              {service.category && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">Category</dt>
                  <dd className="text-safe mt-1">{service.category}</dd>
                </div>
              )}
              {service.duration_minutes && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">Duration</dt>
                  <dd className="text-safe mt-1 flex items-center gap-2">
                    <Clock size={16} />
                    {formatDuration(service.duration_minutes)}
                  </dd>
                </div>
              )}
            </dl>
          </div>

          {/* Group Settings */}
          <div className="bg-calm border border-[0.5px] border-safe p-6">
            <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
              <Users size={20} />
              Group Settings
            </h2>
            {service.group_settings ? (
              <dl className="space-y-3">
                <div>
                  <dt className="text-sm font-medium text-safe-light">Allow Group Sessions</dt>
                  <dd className="text-safe mt-1">
                    {service.group_settings.allow_group_sessions ? (
                      <span className="text-natural">Yes</span>
                    ) : (
                      <span className="text-safe-light">No</span>
                    )}
                  </dd>
                </div>
                {service.group_settings.min_group_size !== null && service.group_settings.min_group_size !== undefined && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">Minimum Group Size</dt>
                    <dd className="text-safe mt-1">{service.group_settings.min_group_size}</dd>
                  </div>
                )}
                {service.group_settings.max_group_size !== null && service.group_settings.max_group_size !== undefined && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">Maximum Group Size</dt>
                    <dd className="text-safe mt-1">{service.group_settings.max_group_size}</dd>
                  </div>
                )}
              </dl>
            ) : (
              <p className="text-safe-light text-sm">No group settings configured</p>
            )}
          </div>

          {/* Metadata */}
          <div className="bg-calm border border-[0.5px] border-safe p-6">
            <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
              <Settings size={20} />
              Metadata
            </h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-safe-light">Created</dt>
                <dd className="text-safe mt-1">
                  {new Date(service.created_at).toLocaleString()}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-safe-light">Last Updated</dt>
                <dd className="text-safe mt-1">
                  {new Date(service.updated_at).toLocaleString()}
                </dd>
              </div>
              {service.metadata && Object.keys(service.metadata).length > 0 && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">Custom Metadata</dt>
                  <dd className="text-safe mt-1">
                    <pre className="text-xs bg-safe-light/10 p-2 rounded overflow-auto">
                      {JSON.stringify(service.metadata, null, 2)}
                    </pre>
                  </dd>
                </div>
              )}
            </dl>
          </div>
        </div>
      </div>
    </AppLayout>
  )
}
