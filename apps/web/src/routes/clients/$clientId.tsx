/**
 * Client Detail Page
 * Displays client information and lifecycle actions
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { StatusBadge } from '@/components/common/StatusBadge'
import { LifecycleActions } from '@/components/common/LifecycleActions'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorDisplay } from '@/components/common/ErrorDisplay'
import { useToast } from '@/contexts/ToastContext'
import { clientsApi } from '@/api/endpoints/clients'
import type { Client } from '@/types/entities'
import type { BaseStatus } from '@/types/enums'
import { Edit, Building2, MapPin, Phone, Mail, Calendar } from 'lucide-react'

export const Route = createFileRoute('/clients/$clientId')({
  component: ClientDetailPage,
})

function ClientDetailPage() {
  const { clientId } = Route.useParams()
  const navigate = useNavigate()
  const { showSuccess, showError } = useToast()
  const [client, setClient] = useState<Client | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchClient = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await clientsApi.getById(clientId)
      setClient(data)
    } catch (err: any) {
      setError(err.message || 'Failed to load client')
      showError('Failed to load client')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchClient()
  }, [clientId])

  const handleAction = async (action: string) => {
    try {
      setActionLoading(true)
      // TODO: Implement actual API calls for lifecycle actions
      showSuccess(`Client ${action} action initiated`)
      await fetchClient()
    } catch (err: any) {
      showError(`Failed to ${action} client`)
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

  if (error || !client) {
    return (
      <AppLayout>
        <div className="max-w-7xl mx-auto">
          <ErrorDisplay
            error={error || 'Client not found'}
            onRetry={fetchClient}
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
            <h1 className="text-3xl font-bold text-safe mb-2">{client.name}</h1>
            <div className="flex items-center gap-4">
              <StatusBadge status={client.status as BaseStatus} />
            </div>
          </div>
          <div className="flex items-center gap-3">
            <LifecycleActions
              currentStatus={client.status}
              onAction={handleAction}
              loading={actionLoading}
            />
            <button
              onClick={() => navigate({ to: `/clients/${clientId}/edit` })}
              className="flex items-center gap-2 px-4 py-2 bg-safe hover:bg-safe-dark text-white rounded-none transition-colors"
            >
              <Edit size={18} />
              <span>Edit</span>
            </button>
          </div>
        </div>

        {/* Client Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* Basic Information */}
          <div className="bg-calm border border-[0.5px] border-safe p-6">
            <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
              <Building2 size={20} />
              Basic Information
            </h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-safe-light">Name</dt>
                <dd className="text-safe mt-1">{client.name}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-safe-light">Status</dt>
                <dd className="text-safe mt-1">
                  <StatusBadge status={client.status as BaseStatus} size="sm" />
                </dd>
              </div>
              {client.industry_id && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">Industry ID</dt>
                  <dd className="text-safe mt-1">{client.industry_id}</dd>
                </div>
              )}
              {client.tax_id && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">Tax ID</dt>
                  <dd className="text-safe mt-1">{client.tax_id}</dd>
                </div>
              )}
              {client.registration_number && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">Registration Number</dt>
                  <dd className="text-safe mt-1">{client.registration_number}</dd>
                </div>
              )}
              {client.parent_client_id && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">Parent Client</dt>
                  <dd className="text-safe mt-1">{client.parent_client_id}</dd>
                </div>
              )}
            </dl>
          </div>

          {/* Contact Information */}
          {client.contact_info && (
            <div className="bg-calm border border-[0.5px] border-safe p-6">
              <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
                <Phone size={20} />
                Contact Information
              </h2>
              <dl className="space-y-3">
                {client.contact_info.email && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light flex items-center gap-2">
                      <Mail size={16} />
                      Email
                    </dt>
                    <dd className="text-safe mt-1">{client.contact_info.email}</dd>
                  </div>
                )}
                {client.contact_info.phone && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light flex items-center gap-2">
                      <Phone size={16} />
                      Phone
                    </dt>
                    <dd className="text-safe mt-1">{client.contact_info.phone}</dd>
                  </div>
                )}
                {client.contact_info.mobile && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">Mobile</dt>
                    <dd className="text-safe mt-1">{client.contact_info.mobile}</dd>
                  </div>
                )}
                {client.contact_info.preferred_method && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">Preferred Method</dt>
                    <dd className="text-safe mt-1">{client.contact_info.preferred_method}</dd>
                  </div>
                )}
              </dl>
            </div>
          )}

          {/* Address */}
          {client.address && (
            <div className="bg-calm border border-[0.5px] border-safe p-6">
              <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
                <MapPin size={20} />
                Address
              </h2>
              <dl className="space-y-3">
                {client.address.street && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">Street</dt>
                    <dd className="text-safe mt-1">{client.address.street}</dd>
                  </div>
                )}
                {client.address.city && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">City</dt>
                    <dd className="text-safe mt-1">{client.address.city}</dd>
                  </div>
                )}
                {client.address.state && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">State</dt>
                    <dd className="text-safe mt-1">{client.address.state}</dd>
                  </div>
                )}
                {client.address.postal_code && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">Postal Code</dt>
                    <dd className="text-safe mt-1">{client.address.postal_code}</dd>
                  </div>
                )}
                {client.address.country && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">Country</dt>
                    <dd className="text-safe mt-1">{client.address.country}</dd>
                  </div>
                )}
              </dl>
            </div>
          )}

          {/* Metadata */}
          <div className="bg-calm border border-[0.5px] border-safe p-6">
            <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
              <Calendar size={20} />
              Metadata
            </h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-safe-light">Created</dt>
                <dd className="text-safe mt-1">
                  {new Date(client.created_at).toLocaleString()}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-safe-light">Last Updated</dt>
                <dd className="text-safe mt-1">
                  {new Date(client.updated_at).toLocaleString()}
                </dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </AppLayout>
  )
}
