/**
 * Create Person Form
 * Reusable form for adding a client employee or dependent. Used in modal and standalone page.
 */

import { useState, useEffect } from 'react'
import { FormField } from '@/components/common/FormField'
import { FormAccordionSection } from '@/components/common/FormAccordionSection'
import { Select } from '@/components/common/Select'
import { DatePicker } from '@/components/common/DatePicker'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useToast } from '@/contexts/ToastContext'
import { personsApi, type PersonCreate } from '@/api/endpoints/persons'
import { clientsApi } from '@/api/endpoints/clients'
import { WorkStatus } from '@/types/enums'
import type { PersonType, RelationType } from '@/types/enums'
import type { Person } from '@/types/entities'

const personTypeOptions = [
  { value: 'ClientEmployee', label: 'Client Employee' },
  { value: 'Dependent', label: 'Dependent' },
]

const relationshipOptions: Array<{ value: RelationType; label: string }> = [
  { value: 'Child', label: 'Child' },
  { value: 'Spouse', label: 'Spouse' },
  { value: 'Parent', label: 'Parent' },
  { value: 'Sibling', label: 'Sibling' },
  { value: 'Grandparent', label: 'Grandparent' },
  { value: 'Guardian', label: 'Guardian' },
  { value: 'Other', label: 'Other' },
]

const genderOptions = [
  { value: '', label: 'Select gender (optional)' },
  { value: 'Male', label: 'Male' },
  { value: 'Female', label: 'Female' },
  { value: 'Non-binary', label: 'Non-binary' },
  { value: 'Other', label: 'Other' },
  { value: 'Prefer not to say', label: 'Prefer not to say' },
]

export interface CreatePersonFormProps {
  /** Pre-fill client (e.g. when adding from client detail). Hides client selector when set. */
  initialClientId?: string
  /** Called after successful create with the created person */
  onSuccess?: (person: Person) => void
  /** Called when user clicks Cancel. When provided, a Cancel button is shown. */
  onCancel?: () => void
}

export function CreatePersonForm({
  initialClientId = '',
  onSuccess,
  onCancel,
}: CreatePersonFormProps) {
  const { showSuccess, showError } = useToast()
  const [loading, setLoading] = useState(false)
  const [clients, setClients] = useState<Array<{ id: string; name: string }>>([])
  const [employees, setEmployees] = useState<Array<{ id: string; name: string; employee_code?: string | null }>>([])
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    middle_name: '',
    person_type: 'ClientEmployee' as PersonType,
    date_of_birth: '',
    gender: '',
    client_id: initialClientId,
    email: '',
    phone: '',
    mobile: '',
    street: '',
    city: '',
    state: '',
    postal_code: '',
    country: '',
    department: '',
    role: '',
    start_date: '',
    status: '' as WorkStatus | '',
    primary_employee_id: '',
    relationship: '' as RelationType | '',
    emergency_contact_name: '',
    emergency_contact_phone: '',
    emergency_contact_email: '',
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    const fetchClients = async () => {
      try {
        const res = await clientsApi.list({ limit: 100 })
        setClients(res.items.map((c) => ({ id: c.id, name: c.name })))
      } catch (err) {
        console.error('Error fetching clients:', err)
      }
    }
    fetchClients()
  }, [])

  useEffect(() => {
    if (initialClientId) setFormData((p) => ({ ...p, client_id: initialClientId }))
  }, [initialClientId])

  useEffect(() => {
    const fetchEmployees = async () => {
      if (!formData.client_id || formData.person_type !== 'Dependent') {
        setEmployees([])
        return
      }
      try {
        const res = await personsApi.list({
          client_id: formData.client_id,
          person_type: 'ClientEmployee',
          limit: 200,
        })
        const employeeList = res.items
          .filter((p: Person) => p.person_type === 'ClientEmployee')
          .map((p: Person) => ({
            id: p.id,
            name: [p.first_name, p.middle_name, p.last_name].filter(Boolean).join(' '),
            employee_code: p.employment_info?.employee_code,
          }))
        setEmployees(employeeList)
      } catch (err) {
        console.error('Error fetching employees:', err)
        setEmployees([])
      }
    }
    fetchEmployees()
  }, [formData.client_id, formData.person_type])

  const validate = () => {
    const next: Record<string, string> = {}
    if (!formData.first_name.trim()) next.first_name = 'First name is required'
    if (!formData.last_name.trim()) next.last_name = 'Last name is required'
    if (!formData.client_id) next.client_id = 'Client is required'
    if (formData.person_type === 'Dependent') {
      if (!formData.primary_employee_id) next.primary_employee_id = 'Primary employee is required'
      if (!formData.relationship) next.relationship = 'Relationship is required'
    }
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return

    try {
      setLoading(true)
      const personData: PersonCreate = {
        first_name: formData.first_name.trim(),
        last_name: formData.last_name.trim(),
        person_type: formData.person_type,
        middle_name: formData.middle_name.trim() || null,
        date_of_birth: formData.date_of_birth || null,
        gender: formData.gender.trim() || null,
        client_id: formData.client_id || null,
      }
      if (formData.email || formData.phone || formData.mobile) {
        personData.contact_info = {
          email: formData.email.trim() || null,
          phone: formData.phone.trim() || null,
          mobile: formData.mobile.trim() || null,
        }
      }
      if (formData.street || formData.city || formData.state || formData.postal_code || formData.country) {
        personData.address = {
          street: formData.street.trim() || null,
          city: formData.city.trim() || null,
          state: formData.state.trim() || null,
          postal_code: formData.postal_code.trim() || null,
          country: formData.country.trim() || null,
        }
      }
      if (formData.person_type === 'ClientEmployee' && (formData.department || formData.role || formData.start_date || formData.status)) {
        personData.employment_info = {
          department: formData.department.trim() || null,
          role: formData.role.trim() || null,
          start_date: formData.start_date || null,
          status: formData.status || null,
        }
      }
      if (formData.person_type === 'Dependent' && formData.primary_employee_id && formData.relationship) {
        personData.dependent_info = {
          primary_employee_id: formData.primary_employee_id,
          relationship: formData.relationship,
          guardian_id: null,
        }
      }
      if (formData.emergency_contact_name || formData.emergency_contact_phone || formData.emergency_contact_email) {
        personData.emergency_contact = {
          name: formData.emergency_contact_name.trim() || null,
          phone: formData.emergency_contact_phone.trim() || null,
          email: formData.emergency_contact_email.trim() || null,
        }
      }

      const created = await personsApi.create(personData)
      showSuccess('Person added to roster')
      onSuccess?.(created)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to add person'
      showError(message)
      const details = err && typeof err === 'object' && 'details' in err && Array.isArray((err as { details: unknown }).details)
        ? (err as { details: Array<{ field?: string; message?: string }> }).details
        : []
      if (details.length > 0) {
        const map: Record<string, string> = {}
        details.forEach((d) => {
          if (d.field) map[d.field] = d.message ?? ''
        })
        setErrors(map)
      }
    } finally {
      setLoading(false)
    }
  }

  const clientOptions = [
    { value: '', label: 'Select client (required)' },
    ...clients.map((c) => ({ value: c.id, label: c.name })),
  ]

  const workStatusOptions = [
    { value: '', label: 'Select status (optional)' },
    { value: WorkStatus.ACTIVE, label: 'Active' },
    { value: WorkStatus.INACTIVE, label: 'Inactive' },
    { value: WorkStatus.ON_LEAVE, label: 'On Leave' },
    { value: WorkStatus.TERMINATED, label: 'Terminated' },
    { value: WorkStatus.SUSPENDED, label: 'Suspended' },
    { value: WorkStatus.RESIGNED, label: 'Resigned' },
  ]

  return (
    <form onSubmit={handleSubmit} className="space-y-2">
      <h3 className="text-sm font-semibold text-text">Basic information</h3>
      <Select
        label="Type"
        name="person_type"
        value={formData.person_type}
        onChange={(v) => setFormData((p) => ({ ...p, person_type: v as PersonType }))}
        options={personTypeOptions}
        compact
      />
      <div className="grid grid-cols-2 gap-2">
        <FormField label="First name" name="first_name" value={formData.first_name} onChange={(e) => { setFormData((p) => ({ ...p, first_name: e.target.value })); if (errors.first_name) setErrors((e2) => ({ ...e2, first_name: '' })) }} error={errors.first_name} required compact />
        <FormField label="Last name" name="last_name" value={formData.last_name} onChange={(e) => { setFormData((p) => ({ ...p, last_name: e.target.value })); if (errors.last_name) setErrors((e2) => ({ ...e2, last_name: '' })) }} error={errors.last_name} required compact />
      </div>
      <FormField label="Middle name" name="middle_name" value={formData.middle_name} onChange={(e) => setFormData((p) => ({ ...p, middle_name: e.target.value }))} compact />
      <DatePicker label="Date of birth" name="date_of_birth" value={formData.date_of_birth} onChange={(v) => setFormData((p) => ({ ...p, date_of_birth: v }))} />
      <Select label="Gender" name="gender" value={formData.gender} onChange={(v) => setFormData((p) => ({ ...p, gender: v }))} options={genderOptions} placeholder="Select gender (optional)" compact />
      {!initialClientId && (
        <Select label="Client" name="client_id" value={formData.client_id} onChange={(v) => { setFormData((p) => ({ ...p, client_id: v as string })); if (errors.client_id) setErrors((e) => ({ ...e, client_id: '' })) }} options={clientOptions} error={errors.client_id} required placeholder="Select client" compact />
      )}

      <FormAccordionSection title="Contact (optional)">
        <FormField label="Email" name="email" type="email" value={formData.email} onChange={(e) => setFormData((p) => ({ ...p, email: e.target.value }))} compact />
        <FormField label="Phone" name="phone" type="tel" value={formData.phone} onChange={(e) => setFormData((p) => ({ ...p, phone: e.target.value }))} compact />
        <FormField label="Mobile" name="mobile" type="tel" value={formData.mobile} onChange={(e) => setFormData((p) => ({ ...p, mobile: e.target.value }))} compact />
      </FormAccordionSection>

      <FormAccordionSection title="Address (optional)">
        <FormField label="Street" name="street" value={formData.street} onChange={(e) => setFormData((p) => ({ ...p, street: e.target.value }))} compact />
        <div className="grid grid-cols-2 gap-2">
          <FormField label="City" name="city" value={formData.city} onChange={(e) => setFormData((p) => ({ ...p, city: e.target.value }))} compact />
          <FormField label="State" name="state" value={formData.state} onChange={(e) => setFormData((p) => ({ ...p, state: e.target.value }))} compact />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <FormField label="Postal code" name="postal_code" value={formData.postal_code} onChange={(e) => setFormData((p) => ({ ...p, postal_code: e.target.value }))} compact />
          <FormField label="Country" name="country" value={formData.country} onChange={(e) => setFormData((p) => ({ ...p, country: e.target.value }))} compact />
        </div>
      </FormAccordionSection>

      {formData.person_type === 'ClientEmployee' && (
        <FormAccordionSection title="Employment (optional)">
          <p className="text-xs text-text-light -mt-1">Employee code will be auto-generated by the system.</p>
          <div className="grid grid-cols-2 gap-2">
            <FormField label="Department" name="department" value={formData.department} onChange={(e) => setFormData((p) => ({ ...p, department: e.target.value }))} compact />
            <FormField label="Role" name="role" value={formData.role} onChange={(e) => setFormData((p) => ({ ...p, role: e.target.value }))} compact />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <DatePicker label="Start date" name="start_date" value={formData.start_date} onChange={(v) => setFormData((p) => ({ ...p, start_date: v }))} />
            <Select label="Work status" name="status" value={formData.status} onChange={(v) => setFormData((p) => ({ ...p, status: v as WorkStatus }))} options={workStatusOptions} compact />
          </div>
        </FormAccordionSection>
      )}

      <FormAccordionSection title="Emergency contact (optional)">
        <FormField label="Name" name="emergency_contact_name" value={formData.emergency_contact_name} onChange={(e) => setFormData((p) => ({ ...p, emergency_contact_name: e.target.value }))} compact />
        <FormField label="Phone" name="emergency_contact_phone" type="tel" value={formData.emergency_contact_phone} onChange={(e) => setFormData((p) => ({ ...p, emergency_contact_phone: e.target.value }))} compact />
        <FormField label="Email" name="emergency_contact_email" type="email" value={formData.emergency_contact_email} onChange={(e) => setFormData((p) => ({ ...p, emergency_contact_email: e.target.value }))} compact />
      </FormAccordionSection>

      {formData.person_type === 'Dependent' && (
        <FormAccordionSection title="Dependent information" defaultOpen>
          <Select label="Primary Employee" name="primary_employee_id" value={formData.primary_employee_id} onChange={(v) => { setFormData((p) => ({ ...p, primary_employee_id: v as string })); if (errors.primary_employee_id) setErrors((e) => ({ ...e, primary_employee_id: '' })) }} options={[{ value: '', label: 'Select primary employee (required)' }, ...employees.map((e) => ({ value: e.id, label: e.employee_code ? `${e.name} (${e.employee_code})` : e.name }))]} error={errors.primary_employee_id} required placeholder="Select primary employee" disabled={!formData.client_id} compact />
          <Select label="Relationship" name="relationship" value={formData.relationship} onChange={(v) => { setFormData((p) => ({ ...p, relationship: v as RelationType })); if (errors.relationship) setErrors((e) => ({ ...e, relationship: '' })) }} options={[{ value: '', label: 'Select relationship (required)' }, ...relationshipOptions]} error={errors.relationship} required placeholder="Select relationship" compact />
        </FormAccordionSection>
      )}

      <div className="flex gap-2 pt-2">
        <button type="submit" disabled={loading} className="flex-1 px-4 py-2 bg-primary hover:bg-primary-hover text-white font-semibold rounded-none transition-colors disabled:opacity-50">
          {loading ? <span className="flex items-center justify-center gap-2"><LoadingSpinner size="sm" color="white" /> Creating...</span> : 'Create'}
        </button>
        {onCancel != null && (
          <button type="button" onClick={onCancel} disabled={loading} className="px-4 py-2 bg-neutral hover:bg-neutral-dark text-white rounded-none transition-colors">Cancel</button>
        )}
      </div>
    </form>
  )
}
