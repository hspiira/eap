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
import type { LifecycleAction } from '@/components/common/LifecycleActions'
import { ArrowLeft, Edit, User, MapPin, Phone, Mail, Calendar, Briefcase, Shield, Users, Link as LinkIcon, CheckCircle, XCircle } from 'lucide-react'

export const Route = createFileRoute('/persons/$personId')({
  component: PersonDetailPage,
})

function PersonDetailPage() {
  const { personId } = Route.useParams()
  const navigate = useNavigate()
  const { showSuccess, showError } = useToast()
  const [person, setPerson] = useState<Person | null>(null)
  const [primaryEmployee, setPrimaryEmployee] = useState<Person | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchPerson = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await personsApi.getById(personId)
      setPerson(data)
      
      // If this is a dependent, fetch the primary employee
      if (data.person_type === 'Dependent' && data.dependent_info?.primary_employee_id) {
        try {
          const primary = await personsApi.getById(data.dependent_info.primary_employee_id)
          setPrimaryEmployee(primary)
        } catch (err) {
          console.error('Failed to load primary employee:', err)
        }
      } else {
        setPrimaryEmployee(null)
      }
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

  const handleAction = async (action: LifecycleAction) => {
    try {
      setActionLoading(true)
      switch (action) {
        case 'activate':
          await personsApi.activate(personId)
          showSuccess('Person activated')
          break
        case 'deactivate':
          await personsApi.deactivate(personId)
          showSuccess('Person deactivated')
          break
        case 'archive':
          await personsApi.archive(personId)
          showSuccess('Person archived')
          break
        case 'restore':
        case 'unarchive':
          await personsApi.restore(personId)
          showSuccess('Person restored')
          break
        default:
          setActionLoading(false)
          return
      }
      await fetchPerson()
    } catch (err: any) {
      showError(err?.message ?? `Failed to ${action} person`)
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
      PlatformStaff: 'Platform Staff',
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
  const backLabel = person.person_type === 'ServiceProvider' ? 'Back to Service providers' : 'Back to Roster'

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        <button
          onClick={() => navigate({ to: backTo })}
          className="flex items-center gap-2 text-text hover:text-primary mb-6 transition-colors"
        >
          <ArrowLeft size={18} />
          <span>{backLabel}</span>
        </button>
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-text mb-2">{getFullName(person)}</h1>
            <div className="flex items-center gap-4">
              <StatusBadge status={person.status as BaseStatus} />
              <span className="text-text-light text-sm">{getPersonTypeLabel(person.person_type)}</span>
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
              className="flex items-center gap-2 px-4 py-2 bg-neutral hover:bg-neutral-dark text-white rounded-none transition-colors"
            >
              <Edit size={18} />
              <span>Edit</span>
            </button>
          </div>
        </div>

        {/* Person Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* Basic Information */}
          <div className="bg-surface border border-[0.5px] border-border p-6">
            <h2 className="text-lg font-semibold text-text mb-4 flex items-center gap-2">
              <User size={20} />
              Basic Information
            </h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-text-light">Full Name</dt>
                <dd className="text-text mt-1">{getFullName(person)}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-text-light">Type</dt>
                <dd className="text-text mt-1">{getPersonTypeLabel(person.person_type)}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-text-light">Status</dt>
                <dd className="text-text mt-1">
                  <StatusBadge status={person.status as BaseStatus} size="sm" />
                </dd>
              </div>
              {person.date_of_birth && (
                <div>
                  <dt className="text-sm font-medium text-text-light">Date of Birth</dt>
                  <dd className="text-text mt-1">
                    {new Date(person.date_of_birth).toLocaleDateString()}
                  </dd>
                </div>
              )}
              {person.gender && (
                <div>
                  <dt className="text-sm font-medium text-text-light">Gender</dt>
                  <dd className="text-text mt-1">{person.gender}</dd>
                </div>
              )}
              {person.is_eligible_for_services != null && (
                <div>
                  <dt className="text-sm font-medium text-text-light">Eligible for services</dt>
                  <dd className="text-text mt-1 flex items-center gap-2">
                    {person.is_eligible_for_services ? (
                      <><CheckCircle size={16} className="text-primary" /> Yes</>
                    ) : (
                      <><XCircle size={16} className="text-text-light" /> No</>
                    )}
                  </dd>
                </div>
              )}
              {person.last_service_date && (
                <div>
                  <dt className="text-sm font-medium text-text-light">Last service date</dt>
                  <dd className="text-text mt-1">
                    {new Date(person.last_service_date).toLocaleDateString()}
                  </dd>
                </div>
              )}
              {person.is_dual_role && person.secondary_person_type && (
                <div>
                  <dt className="text-sm font-medium text-text-light">Dual role</dt>
                  <dd className="text-text mt-1">
                    Also: {getPersonTypeLabel(person.secondary_person_type)}
                  </dd>
                </div>
              )}
            </dl>
          </div>

          {/* Contact Information */}
          {person.contact_info && (
            <div className="bg-surface border border-[0.5px] border-border p-6">
              <h2 className="text-lg font-semibold text-text mb-4 flex items-center gap-2">
                <Phone size={20} />
                Contact Information
              </h2>
              <dl className="space-y-3">
                {person.contact_info.email && (
                  <div>
                    <dt className="text-sm font-medium text-text-light flex items-center gap-2">
                      <Mail size={16} />
                      Email
                    </dt>
                    <dd className="text-text mt-1">{person.contact_info.email}</dd>
                  </div>
                )}
                {person.contact_info.phone && (
                  <div>
                    <dt className="text-sm font-medium text-text-light flex items-center gap-2">
                      <Phone size={16} />
                      Phone
                    </dt>
                    <dd className="text-text mt-1">{person.contact_info.phone}</dd>
                  </div>
                )}
                {person.contact_info.mobile && (
                  <div>
                    <dt className="text-sm font-medium text-text-light">Mobile</dt>
                    <dd className="text-text mt-1">{person.contact_info.mobile}</dd>
                  </div>
                )}
              </dl>
            </div>
          )}

          {/* Employment Information */}
          {person.employment_info && (
            <div className="bg-surface border border-[0.5px] border-border p-6">
              <h2 className="text-lg font-semibold text-text mb-4 flex items-center gap-2">
                <Briefcase size={20} />
                Employment Information
              </h2>
              <dl className="space-y-3">
                {person.employment_info.employee_code && (
                  <div>
                    <dt className="text-sm font-medium text-text-light">Employee Code</dt>
                    <dd className="text-text mt-1">{person.employment_info.employee_code}</dd>
                  </div>
                )}
                {person.employment_info.employee_id && (
                  <div>
                    <dt className="text-sm font-medium text-text-light">Employee ID</dt>
                    <dd className="text-text mt-1">{person.employment_info.employee_id}</dd>
                  </div>
                )}
                {person.employment_info.department && (
                  <div>
                    <dt className="text-sm font-medium text-text-light">Department</dt>
                    <dd className="text-text mt-1">{person.employment_info.department}</dd>
                  </div>
                )}
                {person.employment_info.role && (
                  <div>
                    <dt className="text-sm font-medium text-text-light">Role</dt>
                    <dd className="text-text mt-1">{person.employment_info.role}</dd>
                  </div>
                )}
                {person.employment_info.start_date && (
                  <div>
                    <dt className="text-sm font-medium text-text-light">Start Date</dt>
                    <dd className="text-text mt-1">
                      {new Date(person.employment_info.start_date).toLocaleDateString()}
                    </dd>
                  </div>
                )}
                {person.employment_info.end_date && (
                  <div>
                    <dt className="text-sm font-medium text-text-light">End Date</dt>
                    <dd className="text-text mt-1">
                      {new Date(person.employment_info.end_date).toLocaleDateString()}
                    </dd>
                  </div>
                )}
                {person.employment_info.status && (
                  <div>
                    <dt className="text-sm font-medium text-text-light">Status</dt>
                    <dd className="text-text mt-1">{person.employment_info.status}</dd>
                  </div>
                )}
              </dl>
            </div>
          )}

          {/* Dependent Information */}
          {person.person_type === 'Dependent' && person.dependent_info && (
            <div className="bg-surface border border-[0.5px] border-border p-6">
              <h2 className="text-lg font-semibold text-text mb-4 flex items-center gap-2">
                <LinkIcon size={20} />
                Dependent Information
              </h2>
              <dl className="space-y-3">
                {person.dependent_info.primary_employee_id && (
                  <div>
                    <dt className="text-sm font-medium text-text-light">Primary Employee</dt>
                    <dd className="text-text mt-1">
                      {primaryEmployee ? (
                        <button
                          onClick={() => navigate({ to: `/persons/${person.dependent_info?.primary_employee_id}` })}
                          className="text-primary hover:text-primary-dark font-medium"
                        >
                          {getFullName(primaryEmployee)}
                        </button>
                      ) : (
                        <span>Loading...</span>
                      )}
                    </dd>
                  </div>
                )}
                {person.dependent_info.relationship && (
                  <div>
                    <dt className="text-sm font-medium text-text-light">Relationship</dt>
                    <dd className="text-text mt-1">{person.dependent_info.relationship}</dd>
                  </div>
                )}
                {person.dependent_info.guardian_id && (
                  <div>
                    <dt className="text-sm font-medium text-text-light">Guardian</dt>
                    <dd className="text-text mt-1">{person.dependent_info.guardian_id}</dd>
                  </div>
                )}
              </dl>
            </div>
          )}

          {/* License Information */}
          {person.license_info && (
            <div className="bg-surface border border-[0.5px] border-border p-6">
              <h2 className="text-lg font-semibold text-text mb-4 flex items-center gap-2">
                <Shield size={20} />
                License Information
              </h2>
              <dl className="space-y-3">
                {person.license_info.number && (
                  <div>
                    <dt className="text-sm font-medium text-text-light">License Number</dt>
                    <dd className="text-text mt-1">{person.license_info.number}</dd>
                  </div>
                )}
                {person.license_info.issuing_authority && (
                  <div>
                    <dt className="text-sm font-medium text-text-light">Issuing Authority</dt>
                    <dd className="text-text mt-1">{person.license_info.issuing_authority}</dd>
                  </div>
                )}
                {person.license_info.expiry_date && (
                  <div>
                    <dt className="text-sm font-medium text-text-light">Expiry Date</dt>
                    <dd className="text-text mt-1">
                      {new Date(person.license_info.expiry_date).toLocaleDateString()}
                    </dd>
                  </div>
                )}
              </dl>
            </div>
          )}

          {/* Staff Information */}
          {person.staff_info && (
            <div className="bg-surface border border-[0.5px] border-border p-6">
              <h2 className="text-lg font-semibold text-text mb-4 flex items-center gap-2">
                <Briefcase size={20} />
                Staff Information
              </h2>
              <dl className="space-y-3">
                {person.staff_info.role && (
                  <div>
                    <dt className="text-sm font-medium text-text-light">Role</dt>
                    <dd className="text-text mt-1">{person.staff_info.role}</dd>
                  </div>
                )}
                {person.staff_info.department && (
                  <div>
                    <dt className="text-sm font-medium text-text-light">Department</dt>
                    <dd className="text-text mt-1">{person.staff_info.department}</dd>
                  </div>
                )}
                {person.staff_info.client_id && (
                  <div>
                    <dt className="text-sm font-medium text-text-light">Client</dt>
                    <dd className="text-text mt-1">{person.staff_info.client_id}</dd>
                  </div>
                )}
                {person.staff_info.can_manage_clients != null && (
                  <div>
                    <dt className="text-sm font-medium text-text-light">Can manage clients</dt>
                    <dd className="text-text mt-1">{person.staff_info.can_manage_clients ? 'Yes' : 'No'}</dd>
                  </div>
                )}
                {person.staff_info.can_manage_services != null && (
                  <div>
                    <dt className="text-sm font-medium text-text-light">Can manage services</dt>
                    <dd className="text-text mt-1">{person.staff_info.can_manage_services ? 'Yes' : 'No'}</dd>
                  </div>
                )}
                {person.staff_info.can_view_reports != null && (
                  <div>
                    <dt className="text-sm font-medium text-text-light">Can view reports</dt>
                    <dd className="text-text mt-1">{person.staff_info.can_view_reports ? 'Yes' : 'No'}</dd>
                  </div>
                )}
              </dl>
            </div>
          )}

          {/* Emergency Contact */}
          {person.emergency_contact && (
            <div className="bg-surface border border-[0.5px] border-border p-6">
              <h2 className="text-lg font-semibold text-text mb-4 flex items-center gap-2">
                <Users size={20} />
                Emergency Contact
              </h2>
              <dl className="space-y-3">
                {person.emergency_contact.name && (
                  <div>
                    <dt className="text-sm font-medium text-text-light">Name</dt>
                    <dd className="text-text mt-1">{person.emergency_contact.name}</dd>
                  </div>
                )}
                {person.emergency_contact.phone && (
                  <div>
                    <dt className="text-sm font-medium text-text-light">Phone</dt>
                    <dd className="text-text mt-1">{person.emergency_contact.phone}</dd>
                  </div>
                )}
                {person.emergency_contact.email && (
                  <div>
                    <dt className="text-sm font-medium text-text-light">Email</dt>
                    <dd className="text-text mt-1">{person.emergency_contact.email}</dd>
                  </div>
                )}
              </dl>
            </div>
          )}

          {/* Address */}
          {person.address && (
            <div className="bg-surface border border-[0.5px] border-border p-6">
              <h2 className="text-lg font-semibold text-text mb-4 flex items-center gap-2">
                <MapPin size={20} />
                Address
              </h2>
              <dl className="space-y-3">
                {person.address.street && (
                  <div>
                    <dt className="text-sm font-medium text-text-light">Street</dt>
                    <dd className="text-text mt-1">{person.address.street}</dd>
                  </div>
                )}
                {person.address.city && (
                  <div>
                    <dt className="text-sm font-medium text-text-light">City</dt>
                    <dd className="text-text mt-1">{person.address.city}</dd>
                  </div>
                )}
                {person.address.state && (
                  <div>
                    <dt className="text-sm font-medium text-text-light">State</dt>
                    <dd className="text-text mt-1">{person.address.state}</dd>
                  </div>
                )}
                {person.address.postal_code && (
                  <div>
                    <dt className="text-sm font-medium text-text-light">Postal Code</dt>
                    <dd className="text-text mt-1">{person.address.postal_code}</dd>
                  </div>
                )}
                {person.address.country && (
                  <div>
                    <dt className="text-sm font-medium text-text-light">Country</dt>
                    <dd className="text-text mt-1">{person.address.country}</dd>
                  </div>
                )}
              </dl>
            </div>
          )}

          {/* Metadata */}
          <div className="bg-surface border border-[0.5px] border-border p-6">
            <h2 className="text-lg font-semibold text-text mb-4 flex items-center gap-2">
              <Calendar size={20} />
              Metadata
            </h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-text-light">Created</dt>
                <dd className="text-text mt-1">
                  {new Date(person.created_at).toLocaleString()}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-text-light">Last Updated</dt>
                <dd className="text-text mt-1">
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
