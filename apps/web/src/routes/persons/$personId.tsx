/**
 * Person Detail Page
 * Displays person information and lifecycle actions
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { StatusBadge } from '@/components/common/StatusBadge'
import { LifecycleActions } from '@/components/common/LifecycleActions'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorDisplay } from '@/components/common/ErrorDisplay'
import { useToast } from '@/contexts/ToastContext'
import { personsApi } from '@/api/endpoints/persons'
import type { Person } from '@/types/entities'
import type { BaseStatus, PersonType } from '@/types/enums'
import { ArrowLeft, Edit, User, MapPin, Phone, Mail, Calendar, Briefcase, Shield, Users } from 'lucide-react'

export const Route = createFileRoute('/persons/$personId')({
  component: PersonDetailPage,
})

function PersonDetailPage() {
  const { personId } = Route.useParams()
  const navigate = useNavigate()
  const { showSuccess, showError } = useToast()
  const [person, setPerson] = useState<Person | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchPerson = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await personsApi.getById(personId)
      setPerson(data)
    } catch (err: any) {
      setError(err.message || 'Failed to load person')
      showError('Failed to load person')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPerson()
  }, [personId])

  const handleAction = async (action: string) => {
    try {
      setActionLoading(true)
      // TODO: Implement actual API calls for lifecycle actions
      showSuccess(`Person ${action} action initiated`)
      await fetchPerson()
    } catch (err: any) {
      showError(`Failed to ${action} person`)
    } finally {
      setActionLoading(false)
    }
  }

  const getFullName = (person: Person) => {
    const parts = [person.first_name]
    if (person.middle_name) parts.push(person.middle_name)
    parts.push(person.last_name)
    return parts.join(' ')
  }

  const getPersonTypeLabel = (type: PersonType) => {
    const labels: Record<string, string> = {
      ClientEmployee: 'Client Employee',
      Dependent: 'Dependent',
      ServiceProvider: 'Service Provider',
    }
    return labels[type] || type
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

  if (error || !person) {
    return (
      <AppLayout>
        <div className="max-w-7xl mx-auto">
          <ErrorDisplay
            error={error || 'Person not found'}
            onRetry={fetchPerson}
          />
        </div>
      </AppLayout>
    )
  }

  const backTo = person.person_type === 'ServiceProvider' ? '/service-providers' : '/people/client-people'
  const backLabel = person.person_type === 'ServiceProvider' ? 'Back to Service providers' : 'Back to Client people'

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        <button
          onClick={() => navigate({ to: backTo })}
          className="flex items-center gap-2 text-safe hover:text-natural mb-6 transition-colors"
        >
          <ArrowLeft size={18} />
          <span>{backLabel}</span>
        </button>
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-safe mb-2">{getFullName(person)}</h1>
            <div className="flex items-center gap-4">
              <StatusBadge status={person.status as BaseStatus} />
              <span className="text-safe-light text-sm">{getPersonTypeLabel(person.person_type)}</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <LifecycleActions
              currentStatus={person.status}
              onAction={handleAction}
              loading={actionLoading}
            />
            <button
              onClick={() => navigate({ to: `/persons/${personId}/edit` })}
              className="flex items-center gap-2 px-4 py-2 bg-safe hover:bg-safe-dark text-white rounded-none transition-colors"
            >
              <Edit size={18} />
              <span>Edit</span>
            </button>
          </div>
        </div>

        {/* Person Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* Basic Information */}
          <div className="bg-calm border border-[0.5px] border-safe p-6">
            <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
              <User size={20} />
              Basic Information
            </h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-safe-light">Full Name</dt>
                <dd className="text-safe mt-1">{getFullName(person)}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-safe-light">Type</dt>
                <dd className="text-safe mt-1">{getPersonTypeLabel(person.person_type)}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-safe-light">Status</dt>
                <dd className="text-safe mt-1">
                  <StatusBadge status={person.status as BaseStatus} size="sm" />
                </dd>
              </div>
              {person.date_of_birth && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">Date of Birth</dt>
                  <dd className="text-safe mt-1">
                    {new Date(person.date_of_birth).toLocaleDateString()}
                  </dd>
                </div>
              )}
              {person.gender && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">Gender</dt>
                  <dd className="text-safe mt-1">{person.gender}</dd>
                </div>
              )}
            </dl>
          </div>

          {/* Contact Information */}
          {person.contact_info && (
            <div className="bg-calm border border-[0.5px] border-safe p-6">
              <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
                <Phone size={20} />
                Contact Information
              </h2>
              <dl className="space-y-3">
                {person.contact_info.email && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light flex items-center gap-2">
                      <Mail size={16} />
                      Email
                    </dt>
                    <dd className="text-safe mt-1">{person.contact_info.email}</dd>
                  </div>
                )}
                {person.contact_info.phone && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light flex items-center gap-2">
                      <Phone size={16} />
                      Phone
                    </dt>
                    <dd className="text-safe mt-1">{person.contact_info.phone}</dd>
                  </div>
                )}
                {person.contact_info.mobile && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">Mobile</dt>
                    <dd className="text-safe mt-1">{person.contact_info.mobile}</dd>
                  </div>
                )}
              </dl>
            </div>
          )}

          {/* Employment Information */}
          {person.employment_info && (
            <div className="bg-calm border border-[0.5px] border-safe p-6">
              <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
                <Briefcase size={20} />
                Employment Information
              </h2>
              <dl className="space-y-3">
                {person.employment_info.employee_id && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">Employee ID</dt>
                    <dd className="text-safe mt-1">{person.employment_info.employee_id}</dd>
                  </div>
                )}
                {person.employment_info.department && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">Department</dt>
                    <dd className="text-safe mt-1">{person.employment_info.department}</dd>
                  </div>
                )}
                {person.employment_info.position && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">Position</dt>
                    <dd className="text-safe mt-1">{person.employment_info.position}</dd>
                  </div>
                )}
                {person.employment_info.hire_date && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">Hire Date</dt>
                    <dd className="text-safe mt-1">
                      {new Date(person.employment_info.hire_date).toLocaleDateString()}
                    </dd>
                  </div>
                )}
                {person.employment_info.work_status && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">Work Status</dt>
                    <dd className="text-safe mt-1">{person.employment_info.work_status}</dd>
                  </div>
                )}
              </dl>
            </div>
          )}

          {/* License Information */}
          {person.license_info && (
            <div className="bg-calm border border-[0.5px] border-safe p-6">
              <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
                <Shield size={20} />
                License Information
              </h2>
              <dl className="space-y-3">
                {person.license_info.license_number && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">License Number</dt>
                    <dd className="text-safe mt-1">{person.license_info.license_number}</dd>
                  </div>
                )}
                {person.license_info.license_type && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">License Type</dt>
                    <dd className="text-safe mt-1">{person.license_info.license_type}</dd>
                  </div>
                )}
                {person.license_info.issuing_authority && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">Issuing Authority</dt>
                    <dd className="text-safe mt-1">{person.license_info.issuing_authority}</dd>
                  </div>
                )}
                {person.license_info.issue_date && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">Issue Date</dt>
                    <dd className="text-safe mt-1">
                      {new Date(person.license_info.issue_date).toLocaleDateString()}
                    </dd>
                  </div>
                )}
                {person.license_info.expiry_date && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">Expiry Date</dt>
                    <dd className="text-safe mt-1">
                      {new Date(person.license_info.expiry_date).toLocaleDateString()}
                    </dd>
                  </div>
                )}
              </dl>
            </div>
          )}

          {/* Emergency Contact */}
          {person.emergency_contact && (
            <div className="bg-calm border border-[0.5px] border-safe p-6">
              <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
                <Users size={20} />
                Emergency Contact
              </h2>
              <dl className="space-y-3">
                {person.emergency_contact.name && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">Name</dt>
                    <dd className="text-safe mt-1">{person.emergency_contact.name}</dd>
                  </div>
                )}
                {person.emergency_contact.relationship && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">Relationship</dt>
                    <dd className="text-safe mt-1">{person.emergency_contact.relationship}</dd>
                  </div>
                )}
                {person.emergency_contact.phone && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">Phone</dt>
                    <dd className="text-safe mt-1">{person.emergency_contact.phone}</dd>
                  </div>
                )}
              </dl>
            </div>
          )}

          {/* Address */}
          {person.address && (
            <div className="bg-calm border border-[0.5px] border-safe p-6">
              <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
                <MapPin size={20} />
                Address
              </h2>
              <dl className="space-y-3">
                {person.address.street && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">Street</dt>
                    <dd className="text-safe mt-1">{person.address.street}</dd>
                  </div>
                )}
                {person.address.city && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">City</dt>
                    <dd className="text-safe mt-1">{person.address.city}</dd>
                  </div>
                )}
                {person.address.state && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">State</dt>
                    <dd className="text-safe mt-1">{person.address.state}</dd>
                  </div>
                )}
                {person.address.postal_code && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">Postal Code</dt>
                    <dd className="text-safe mt-1">{person.address.postal_code}</dd>
                  </div>
                )}
                {person.address.country && (
                  <div>
                    <dt className="text-sm font-medium text-safe-light">Country</dt>
                    <dd className="text-safe mt-1">{person.address.country}</dd>
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
                  {new Date(person.created_at).toLocaleString()}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-safe-light">Last Updated</dt>
                <dd className="text-safe mt-1">
                  {new Date(person.updated_at).toLocaleString()}
                </dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </AppLayout>
  )
}
