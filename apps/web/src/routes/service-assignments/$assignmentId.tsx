/**
 * Service Assignment Detail Page
 * Displays assignment information and lifecycle actions
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { StatusBadge } from '@/components/common/StatusBadge'
import { LifecycleActions } from '@/components/common/LifecycleActions'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorDisplay } from '@/components/common/ErrorDisplay'
import { useToast } from '@/contexts/ToastContext'
import { serviceAssignmentsApi } from '@/api/endpoints/service-assignments'
import { contractsApi } from '@/api/endpoints/contracts'
import { servicesApi } from '@/api/endpoints/services'
import type { ServiceAssignment } from '@/types/entities'
import type { BaseStatus } from '@/types/enums'
import { Link, Calendar, Package, FileText } from 'lucide-react'

export const Route = createFileRoute('/service-assignments/$assignmentId')({
  component: ServiceAssignmentDetailPage,
})

function ServiceAssignmentDetailPage() {
  const { assignmentId } = Route.useParams()
  const navigate = useNavigate()
  const { showSuccess, showError } = useToast()
  const [assignment, setAssignment] = useState<ServiceAssignment | null>(null)
  const [contract, setContract] = useState<{ id: string; name: string } | null>(null)
  const [service, setService] = useState<{ id: string; name: string } | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchAssignment = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await serviceAssignmentsApi.getById(assignmentId)
      setAssignment(data)

      // Fetch contract and service info
      try {
        const [contractData, serviceData] = await Promise.all([
          contractsApi.getById(data.contract_id),
          servicesApi.getById(data.service_id),
        ])
        setContract({ 
          id: contractData.id, 
          name: contractData.contract_number || `Contract #${contractData.id.slice(0, 8)}` 
        })
        setService({ id: serviceData.id, name: serviceData.name })
      } catch (err) {
        console.error('Error fetching related data:', err)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load assignment')
      showError('Failed to load assignment')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAssignment()
  }, [assignmentId])

  const handleAction = async (action: string) => {
    try {
      setActionLoading(true)
      let updatedAssignment: ServiceAssignment

      switch (action) {
        case 'activate':
          updatedAssignment = await serviceAssignmentsApi.activate(assignmentId)
          break
        case 'deactivate':
          updatedAssignment = await serviceAssignmentsApi.deactivate(assignmentId)
          break
        case 'archive':
          updatedAssignment = await serviceAssignmentsApi.archive(assignmentId)
          break
        case 'restore':
          updatedAssignment = await serviceAssignmentsApi.restore(assignmentId)
          break
        default:
          throw new Error(`Unknown action: ${action}`)
      }

      setAssignment(updatedAssignment)
      showSuccess(`Assignment ${action}d successfully`)
    } catch (err: any) {
      showError(`Failed to ${action} assignment: ${err.message || 'Unknown error'}`)
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

  if (error || !assignment) {
    return (
      <AppLayout>
        <div className="max-w-7xl mx-auto">
          <ErrorDisplay
            error={error || 'Assignment not found'}
            onRetry={fetchAssignment}
          />
        </div>
      </AppLayout>
    )
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
            <h1 className="text-3xl font-bold text-safe mb-2">Service Assignment</h1>
            <div className="flex items-center gap-4">
              <StatusBadge status={assignment.status as BaseStatus} />
            </div>
          </div>
          <div className="flex items-center gap-3">
            <LifecycleActions
              currentStatus={assignment.status}
              onAction={handleAction}
              loading={actionLoading}
            />
            <button
              onClick={() => navigate({ to: `/service-assignments/${assignmentId}/edit` })}
              className="flex items-center gap-2 px-4 py-2 bg-safe hover:bg-safe-dark text-white rounded-none transition-colors"
            >
              <FileText size={18} />
              <span>Edit</span>
            </button>
          </div>
        </div>

        {/* Assignment Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* Assignment Details */}
          <div className="bg-calm border border-[0.5px] border-safe/30 p-6">
            <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
              <Link size={20} />
              Assignment Details
            </h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-safe-light">Status</dt>
                <dd className="text-safe mt-1">
                  <StatusBadge status={assignment.status as BaseStatus} size="sm" />
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-safe-light">Contract</dt>
                <dd className="text-safe mt-1">
                  {contract ? (
                    <button
                      onClick={() => navigate({ to: `/contracts/${assignment.contract_id}` })}
                      className="text-natural hover:text-natural-dark font-medium"
                    >
                      {contract.name}
                    </button>
                  ) : (
                    assignment.contract_id
                  )}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-safe-light">Service</dt>
                <dd className="text-safe mt-1">
                  {service ? (
                    <button
                      onClick={() => navigate({ to: `/services/${assignment.service_id}` })}
                      className="text-natural hover:text-natural-dark font-medium"
                    >
                      {service.name}
                    </button>
                  ) : (
                    assignment.service_id
                  )}
                </dd>
              </div>
            </dl>
          </div>

          {/* Date Information */}
          <div className="bg-calm border border-[0.5px] border-safe/30 p-6">
            <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
              <Calendar size={20} />
              Date Information
            </h2>
            <dl className="space-y-3">
              {assignment.start_date && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">Start Date</dt>
                  <dd className="text-safe mt-1 flex items-center gap-2">
                    <Calendar size={16} />
                    {formatDate(assignment.start_date)}
                  </dd>
                </div>
              )}
              {assignment.end_date && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">End Date</dt>
                  <dd className="text-safe mt-1 flex items-center gap-2">
                    <Calendar size={16} />
                    {formatDate(assignment.end_date)}
                  </dd>
                </div>
              )}
            </dl>
          </div>

          {/* Metadata */}
          <div className="bg-calm border border-[0.5px] border-safe/30 p-6">
            <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
              <Package size={20} />
              Metadata
            </h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-safe-light">Created</dt>
                <dd className="text-safe mt-1">
                  {new Date(assignment.created_at).toLocaleString()}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-safe-light">Last Updated</dt>
                <dd className="text-safe mt-1">
                  {new Date(assignment.updated_at).toLocaleString()}
                </dd>
              </div>
              {assignment.metadata && Object.keys(assignment.metadata).length > 0 && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">Custom Metadata</dt>
                  <dd className="text-safe mt-1">
                    <pre className="text-xs bg-safe-light/10 p-2 rounded overflow-auto">
                      {JSON.stringify(assignment.metadata, null, 2)}
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
