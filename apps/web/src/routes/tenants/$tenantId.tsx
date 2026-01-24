/**
 * Tenant Detail Page
 * Displays tenant information and lifecycle actions
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { StatusBadge } from '@/components/common/StatusBadge'
import { LifecycleActions } from '@/components/common/LifecycleActions'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorDisplay } from '@/components/common/ErrorDisplay'
import { useToast } from '@/contexts/ToastContext'
import { tenantsApi } from '@/api/endpoints/tenants'
import type { Tenant } from '@/types/entities'
import type { TenantStatus } from '@/types/enums'
import { Edit, Building2, Calendar, MapPin, Phone, Mail } from 'lucide-react'

export const Route = createFileRoute('/tenants/$tenantId')({
  component: TenantDetailPage,
})

function TenantDetailPage() {
  const { tenantId } = Route.useParams()
  const navigate = useNavigate()
  const { showSuccess, showError } = useToast()
  const [tenant, setTenant] = useState<Tenant | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchTenant = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await tenantsApi.getById(tenantId)
      setTenant(data)
    } catch (err: any) {
      setError(err.message || 'Failed to load tenant')
      showError('Failed to load tenant')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTenant()
  }, [tenantId])

  const handleAction = async (action: string) => {
    try {
      setActionLoading(true)
      // TODO: Implement actual API calls for lifecycle actions
      // For now, just show a message
      showSuccess(`Tenant ${action} action initiated`)
      // Refresh tenant data
      await fetchTenant()
    } catch (err: any) {
      showError(`Failed to ${action} tenant`)
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

  if (error || !tenant) {
    return (
      <AppLayout>
        <div className="max-w-7xl mx-auto">
          <ErrorDisplay
            error={error || 'Tenant not found'}
            onRetry={fetchTenant}
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
            <h1 className="text-3xl font-bold text-safe mb-2">{tenant.name}</h1>
            <div className="flex items-center gap-4">
              <StatusBadge status={tenant.status as TenantStatus} />
              <span className="text-safe-light text-sm">Code: {tenant.code || 'N/A'}</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <LifecycleActions
              currentStatus={tenant.status}
              onAction={handleAction}
              loading={actionLoading}
            />
            <button
              onClick={() => navigate({ to: `/tenants/${tenantId}/edit` })}
              className="flex items-center gap-2 px-4 py-2 bg-safe hover:bg-safe-dark text-white rounded-none transition-colors"
            >
              <Edit size={18} />
              <span>Edit</span>
            </button>
          </div>
        </div>

        {/* Tenant Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* Basic Information */}
          <div className="bg-calm border border-[0.5px] border-safe/30 p-6">
            <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
              <Building2 size={20} />
              Basic Information
            </h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-safe-light">Name</dt>
                <dd className="text-safe mt-1">{tenant.name}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-safe-light">Code</dt>
                <dd className="text-safe mt-1 font-mono">{tenant.code || 'N/A'}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-safe-light">Status</dt>
                <dd className="text-safe mt-1">
                  <StatusBadge status={tenant.status as TenantStatus} size="sm" />
                </dd>
              </div>
              {tenant.industry_id && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">Industry ID</dt>
                  <dd className="text-safe mt-1">{tenant.industry_id}</dd>
                </div>
              )}
            </dl>
          </div>

          {/* Contact Information */}
          {tenant.contact_info && (
            <div className="bg-calm border border-[0.5px] border-safe/30 p-6">
              <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
                <Phone size={20} />
                Contact Information
              </h2>
              <dl className="space-y-3">
                {tenant.contact_info.email && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light flex items-center gap-2">
                      <Mail size={16} />
                      Email
                    </dt>
                    <dd className="text-safe mt-1">{tenant.contact_info.email}</dd>
                  </div>
                )}
                {tenant.contact_info.phone && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light flex items-center gap-2">
                      <Phone size={16} />
                      Phone
                    </dt>
                    <dd className="text-safe mt-1">{tenant.contact_info.phone}</dd>
                  </div>
                )}
                {tenant.contact_info.mobile && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">Mobile</dt>
                    <dd className="text-safe mt-1">{tenant.contact_info.mobile}</dd>
                  </div>
                )}
              </dl>
            </div>
          )}

          {/* Address */}
          {tenant.address && (
            <div className="bg-calm border border-[0.5px] border-safe/30 p-6">
              <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
                <MapPin size={20} />
                Address
              </h2>
              <dl className="space-y-3">
                {tenant.address.street && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">Street</dt>
                    <dd className="text-safe mt-1">{tenant.address.street}</dd>
                  </div>
                )}
                {tenant.address.city && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">City</dt>
                    <dd className="text-safe mt-1">{tenant.address.city}</dd>
                  </div>
                )}
                {tenant.address.state && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">State</dt>
                    <dd className="text-safe mt-1">{tenant.address.state}</dd>
                  </div>
                )}
                {tenant.address.postal_code && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">Postal Code</dt>
                    <dd className="text-safe mt-1">{tenant.address.postal_code}</dd>
                  </div>
                )}
                {tenant.address.country && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">Country</dt>
                    <dd className="text-safe mt-1">{tenant.address.country}</dd>
                  </div>
                )}
              </dl>
            </div>
          )}

          {/* Metadata */}
          <div className="bg-calm border border-[0.5px] border-safe/30 p-6">
            <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
              <Calendar size={20} />
              Metadata
            </h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-safe-light">Created</dt>
                <dd className="text-safe mt-1">
                  {new Date(tenant.created_at).toLocaleString()}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-safe-light">Last Updated</dt>
                <dd className="text-safe mt-1">
                  {new Date(tenant.updated_at).toLocaleString()}
                </dd>
              </div>
              {tenant.status_changed_at && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">Status Changed</dt>
                  <dd className="text-safe mt-1">
                    {new Date(tenant.status_changed_at).toLocaleString()}
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
