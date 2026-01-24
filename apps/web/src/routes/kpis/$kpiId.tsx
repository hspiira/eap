/**
 * KPI Detail Page
 * Displays KPI information, assignments to clients/contracts, and optional visualization
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorDisplay } from '@/components/common/ErrorDisplay'
import { FormField } from '@/components/common/FormField'
import { Select } from '@/components/common/Select'
import { DatePicker } from '@/components/common/DatePicker'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { useToast } from '@/contexts/ToastContext'
import { kpisApi } from '@/api/endpoints/kpis'
import { clientsApi } from '@/api/endpoints/clients'
import { contractsApi } from '@/api/endpoints/contracts'
import type { KPI, KPIAssignment } from '@/types/entities'
import type { MeasurementUnit } from '@/types/enums'
import { Target, TrendingUp, Building2, FileText, Plus, Calendar } from 'lucide-react'

export const Route = createFileRoute('/kpis/$kpiId')({
  component: KPIDetailPage,
})

function KPIDetailPage() {
  const { kpiId } = Route.useParams()
  const navigate = useNavigate()
  const { showSuccess, showError } = useToast()
  const [kpi, setKpi] = useState<KPI | null>(null)
  const [assignments, setAssignments] = useState<KPIAssignment[]>([])
  const [clients, setClients] = useState<Array<{ id: string; name: string }>>([])
  const [contracts, setContracts] = useState<Array<{ id: string; name: string }>>([])
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showAssignDialog, setShowAssignDialog] = useState(false)
  const [assignFormData, setAssignFormData] = useState({
    assignable_type: 'Client' as 'Client' | 'Contract',
    assignable_id: '',
    target_value: '',
    start_date: '',
    end_date: '',
  })

  const fetchKPI = async () => {
    try {
      setLoading(true)
      setError(null)
      const [kpiData, assignmentsData] = await Promise.all([
        kpisApi.getById(kpiId),
        kpisApi.getAssignments(kpiId),
      ])
      setKpi(kpiData)
      setAssignments(assignmentsData)

      // Fetch clients and contracts for assignment dropdowns
      try {
        const [clientsResponse, contractsResponse] = await Promise.all([
          clientsApi.list({ limit: 100 }),
          contractsApi.list({ limit: 100 }),
        ])
        setClients(clientsResponse.items.map(c => ({ id: c.id, name: c.name })))
        setContracts(contractsResponse.items.map(c => ({ 
          id: c.id, 
          name: c.contract_number || `Contract #${c.id.slice(0, 8)}` 
        })))
      } catch (err) {
        console.error('Error fetching clients/contracts:', err)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load KPI')
      showError('Failed to load KPI')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchKPI()
  }, [kpiId])

  const handleAssign = async () => {
    if (!assignFormData.assignable_id) {
      showError('Please select a client or contract')
      return
    }

    try {
      setActionLoading(true)
      await kpisApi.assign(kpiId, {
        assignable_type: assignFormData.assignable_type,
        assignable_id: assignFormData.assignable_id,
        target_value: assignFormData.target_value ? parseFloat(assignFormData.target_value) : null,
        start_date: assignFormData.start_date || null,
        end_date: assignFormData.end_date || null,
      })
      setShowAssignDialog(false)
      setAssignFormData({
        assignable_type: 'Client',
        assignable_id: '',
        target_value: '',
        start_date: '',
        end_date: '',
      })
      showSuccess('KPI assigned successfully')
      fetchKPI()
    } catch (err: any) {
      showError(`Failed to assign KPI: ${err.message || 'Unknown error'}`)
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

  if (error || !kpi) {
    return (
      <AppLayout>
        <div className="max-w-7xl mx-auto">
          <ErrorDisplay
            error={error || 'KPI not found'}
            onRetry={fetchKPI}
          />
        </div>
      </AppLayout>
    )
  }

  const formatValue = (value: number | null | undefined) => {
    if (value === null || value === undefined) return '-'
    switch (kpi.measurement_unit) {
      case 'Percentage':
        return `${value}%`
      case 'Currency':
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value)
      case 'Time':
        return `${value} min`
      default:
        return value.toString()
    }
  }

  const getProgressPercentage = (current: number | null | undefined, target: number | null | undefined) => {
    if (!current || !target || target === 0) return null
    return Math.min((current / target) * 100, 100)
  }

  const progress = getProgressPercentage(kpi.current_value, kpi.target_value)

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-safe mb-2 flex items-center gap-2">
              <Target size={28} />
              {kpi.name}
            </h1>
            <div className="flex items-center gap-4">
              <span className="text-safe-light">{kpi.category}</span>
              <span className="text-safe-light text-sm">•</span>
              <span className="text-safe-light text-sm">{kpi.measurement_unit}</span>
            </div>
          </div>
          <button
            onClick={() => setShowAssignDialog(true)}
            className="flex items-center gap-2 px-4 py-2 bg-natural hover:bg-natural-dark text-white rounded-none transition-colors"
          >
            <Plus size={18} />
            <span>Assign KPI</span>
          </button>
        </div>

        {/* KPI Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* KPI Details */}
          <div className="bg-calm border border-[0.5px] border-safe p-6">
            <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
              <Target size={20} />
              KPI Details
            </h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-safe-light">Name</dt>
                <dd className="text-safe mt-1">{kpi.name}</dd>
              </div>
              {kpi.description && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">Description</dt>
                  <dd className="text-safe mt-1">{kpi.description}</dd>
                </div>
              )}
              <div>
                <dt className="text-sm font-medium text-safe-light">Category</dt>
                <dd className="text-safe mt-1">{kpi.category}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-safe-light">Measurement Unit</dt>
                <dd className="text-safe mt-1">{kpi.measurement_unit}</dd>
              </div>
            </dl>
          </div>

          {/* Performance Metrics */}
          <div className="bg-calm border border-[0.5px] border-safe p-6">
            <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
              <TrendingUp size={20} />
              Performance
            </h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-safe-light">Target Value</dt>
                <dd className="text-safe mt-1 text-lg font-semibold">
                  {formatValue(kpi.target_value)}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-safe-light">Current Value</dt>
                <dd className="text-safe mt-1 text-lg font-semibold">
                  {formatValue(kpi.current_value)}
                </dd>
              </div>
              {progress !== null && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">Progress</dt>
                  <dd className="mt-2">
                    <div className="w-full h-4 bg-safe-light rounded-full overflow-hidden">
                      <div
                        className={`h-full ${
                          progress >= 100 ? 'bg-natural' : progress >= 75 ? 'bg-safe' : 'bg-nurturing'
                        }`}
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                    <span className="text-sm text-safe-light mt-1 block">
                      {progress.toFixed(1)}%
                    </span>
                  </dd>
                </div>
              )}
            </dl>
          </div>

          {/* Assignments */}
          <div className="bg-calm border border-[0.5px] border-safe p-6 md:col-span-2">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-safe flex items-center gap-2">
                <FileText size={20} />
                Assignments
              </h2>
            </div>
            {assignments.length > 0 ? (
              <div className="space-y-2">
                {assignments.map((assignment) => {
                  const assignable = assignment.assignable_type === 'Client'
                    ? clients.find(c => c.id === assignment.assignable_id)
                    : contracts.find(c => c.id === assignment.assignable_id)
                  
                  return (
                    <div
                      key={assignment.id}
                      className="flex items-center justify-between p-3 bg-safe-light/5 border border-[0.5px] border-safe"
                    >
                      <div className="flex items-center gap-3">
                        {assignment.assignable_type === 'Client' ? (
                          <Building2 size={20} className="text-natural" />
                        ) : (
                          <FileText size={20} className="text-natural" />
                        )}
                        <div>
                          <p className="font-medium text-safe">
                            {assignable?.name || assignment.assignable_id}
                          </p>
                          <p className="text-safe-light text-sm">
                            {assignment.assignable_type}
                            {assignment.target_value && ` • Target: ${formatValue(assignment.target_value)}`}
                          </p>
                        </div>
                      </div>
                      <div className="text-safe-light text-sm">
                        {assignment.start_date && (
                          <span className="flex items-center gap-1">
                            <Calendar size={14} />
                            {new Date(assignment.start_date).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : (
              <p className="text-safe-light text-sm">No assignments yet</p>
            )}
          </div>
        </div>

        {/* Assign Dialog */}
        {showAssignDialog && (
          <ConfirmDialog
            title="Assign KPI"
            message="Assign this KPI to a client or contract"
            onConfirm={handleAssign}
            onCancel={() => {
              setShowAssignDialog(false)
              setAssignFormData({
                assignable_type: 'Client',
                assignable_id: '',
                target_value: '',
                start_date: '',
                end_date: '',
              })
            }}
            confirmText="Assign"
            cancelText="Cancel"
            loading={actionLoading}
          >
            <div className="space-y-4 mt-4">
              <Select
                label="Assign To"
                name="assignable_type"
                value={assignFormData.assignable_type}
                onChange={(value) => {
                  setAssignFormData({ ...assignFormData, assignable_type: value as 'Client' | 'Contract', assignable_id: '' })
                }}
                options={[
                  { value: 'Client', label: 'Client' },
                  { value: 'Contract', label: 'Contract' },
                ]}
                required
              />

              <Select
                label={assignFormData.assignable_type}
                name="assignable_id"
                value={assignFormData.assignable_id}
                onChange={(value) => setAssignFormData({ ...assignFormData, assignable_id: value as string })}
                options={[
                  { value: '', label: `Select ${assignFormData.assignable_type.toLowerCase()}` },
                  ...(assignFormData.assignable_type === 'Client'
                    ? clients.map(c => ({ value: c.id, label: c.name }))
                    : contracts.map(c => ({ value: c.id, label: c.name }))),
                ]}
                required
              />

              <FormField
                label="Target Value (optional)"
                name="target_value"
                type="number"
                value={assignFormData.target_value}
                onChange={(e) => setAssignFormData({ ...assignFormData, target_value: e.target.value })}
                placeholder="Override default target value"
              />

              <DatePicker
                label="Start Date (optional)"
                name="start_date"
                value={assignFormData.start_date}
                onChange={(value) => setAssignFormData({ ...assignFormData, start_date: value })}
              />

              <DatePicker
                label="End Date (optional)"
                name="end_date"
                value={assignFormData.end_date}
                onChange={(value) => setAssignFormData({ ...assignFormData, end_date: value })}
              />
            </div>
          </ConfirmDialog>
        )}
      </div>
    </AppLayout>
  )
}
