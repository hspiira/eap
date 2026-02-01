/**
 * Contract Detail Page
 * Displays contract information, billing details, renewal history, and lifecycle actions
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { StatusBadge } from '@/components/common/StatusBadge'
import { LifecycleActions } from '@/components/common/LifecycleActions'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorDisplay } from '@/components/common/ErrorDisplay'
import { useToast } from '@/contexts/ToastContext'
import { contractsApi } from '@/api/endpoints/contracts'
import { clientsApi } from '@/api/endpoints/clients'
import type { Contract } from '@/types/entities'
import type { ContractStatus, PaymentStatus } from '@/types/enums'
import { Edit, FileText, DollarSign, Calendar, RefreshCw, Building2 } from 'lucide-react'

export const Route = createFileRoute('/contracts/$contractId')({
  component: ContractDetailPage,
})

function ContractDetailPage() {
  const { contractId } = Route.useParams()
  const navigate = useNavigate()
  const { showSuccess, showError } = useToast()
  const [contract, setContract] = useState<Contract | null>(null)
  const [client, setClient] = useState<{ id: string; name: string } | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchContract = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await contractsApi.getById(contractId)
      setContract(data)

      // Fetch client info
      try {
        const clientData = await clientsApi.getById(data.client_id)
        setClient({ id: clientData.id, name: clientData.name })
      } catch (err) {
        console.error('Error fetching client:', err)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load contract')
      showError('Failed to load contract')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchContract()
  }, [contractId])

  const handleAction = async (action: string) => {
    try {
      setActionLoading(true)
      // TODO: Implement actual API calls for lifecycle actions (activate, renew, terminate)
      showSuccess(`Contract ${action} action initiated`)
      await fetchContract()
    } catch (err: any) {
      showError(`Failed to ${action} contract`)
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

  if (error || !contract) {
    return (
      <AppLayout>
        <div className="max-w-7xl mx-auto">
          <ErrorDisplay
            error={error || 'Contract not found'}
            onRetry={fetchContract}
          />
        </div>
      </AppLayout>
    )
  }

  const formatCurrency = (amount: number | null | undefined, currency: string | null | undefined) => {
    if (!amount) return '-'
    const curr = currency || 'USD'
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: curr }).format(amount)
  }

  const formatDate = (date: string | null | undefined) => {
    if (!date) return '-'
    return new Date(date).toLocaleDateString()
  }

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-safe mb-2">
              {contract.contract_number || `Contract #${contract.id.slice(0, 8)}`}
            </h1>
            <div className="flex items-center gap-4">
              <StatusBadge status={contract.status as ContractStatus} />
              {client && (
                <span className="text-safe-light text-sm flex items-center gap-1">
                  <Building2 size={16} />
                  {client.name}
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-3">
            <LifecycleActions
              currentStatus={contract.status}
              onAction={handleAction}
              loading={actionLoading}
            />
            <button
              onClick={() => navigate({ to: `/contracts/${contractId}/edit` })}
              className="flex items-center gap-2 px-4 py-2 bg-neutral hover:bg-neutral-dark text-white rounded-none transition-colors"
            >
              <Edit size={18} />
              <span>Edit</span>
            </button>
          </div>
        </div>

        {/* Contract Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* Contract Details */}
          <div className="bg-white border border-[0.5px] border-safe/30 p-6">
            <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
              <FileText size={20} />
              Contract Details
            </h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-safe-light">Contract Number</dt>
                <dd className="text-safe mt-1">{contract.contract_number || `#${contract.id.slice(0, 8)}`}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-safe-light">Status</dt>
                <dd className="text-safe mt-1">
                  <StatusBadge status={contract.status as ContractStatus} size="sm" />
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-safe-light">Client</dt>
                <dd className="text-safe mt-1">{client?.name || contract.client_id}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-safe-light">Start Date</dt>
                <dd className="text-safe mt-1 flex items-center gap-2">
                  <Calendar size={16} />
                  {formatDate(contract.start_date)}
                </dd>
              </div>
              {contract.end_date && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">End Date</dt>
                  <dd className="text-safe mt-1 flex items-center gap-2">
                    <Calendar size={16} />
                    {formatDate(contract.end_date)}
                  </dd>
                </div>
              )}
              {contract.renewal_date && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">Renewal Date</dt>
                  <dd className="text-safe mt-1 flex items-center gap-2">
                    <RefreshCw size={16} />
                    {formatDate(contract.renewal_date)}
                  </dd>
                </div>
              )}
            </dl>
          </div>

          {/* Billing Information */}
          <div className="bg-white border border-[0.5px] border-safe/30 p-6">
            <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
              <DollarSign size={20} />
              Billing Information
            </h2>
            <dl className="space-y-3">
              {contract.billing_amount !== null && contract.billing_amount !== undefined && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">Billing Amount</dt>
                  <dd className="text-safe mt-1 text-lg font-semibold">
                    {formatCurrency(contract.billing_amount, contract.currency)}
                  </dd>
                </div>
              )}
              {contract.billing_frequency && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">Billing Frequency</dt>
                  <dd className="text-safe mt-1">{contract.billing_frequency}</dd>
                </div>
              )}
              {contract.currency && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">Currency</dt>
                  <dd className="text-safe mt-1">{contract.currency}</dd>
                </div>
              )}
              {contract.payment_status && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">Payment Status</dt>
                  <dd className="text-safe mt-1">
                    <StatusBadge status={contract.payment_status as PaymentStatus} size="sm" />
                  </dd>
                </div>
              )}
            </dl>
          </div>

          {/* Renewal History */}
          <div className="bg-white border border-[0.5px] border-safe/30 p-6 md:col-span-2">
            <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
              <RefreshCw size={20} />
              Renewal History
            </h2>
            <p className="text-safe-light text-sm">
              Renewal history will be displayed here once renewal tracking is implemented.
            </p>
            {/* TODO: Implement renewal history display when API endpoint is available */}
          </div>

          {/* Metadata */}
          <div className="bg-white border border-[0.5px] border-safe/30 p-6">
            <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
              <Calendar size={20} />
              Metadata
            </h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-safe-light">Created</dt>
                <dd className="text-safe mt-1">
                  {new Date(contract.created_at).toLocaleString()}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-safe-light">Last Updated</dt>
                <dd className="text-safe mt-1">
                  {new Date(contract.updated_at).toLocaleString()}
                </dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </AppLayout>
  )
}
