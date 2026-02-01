/**
 * Persons API Endpoints
 */

import apiClient from '../client'
import type { Person, PaginatedResponse, ListParams } from '../types'
import type { PersonType, RelationType } from '@/types/enums'
import type {
  Address,
  EmploymentInfo,
  DependentInfo,
  LicenseInfo,
  StaffInfo,
  EmergencyContact,
} from '@/types/entities'

export interface PersonCreate {
  first_name: string
  last_name: string
  middle_name?: string | null
  person_type: PersonType
  date_of_birth?: string | null
  gender?: string | null
  client_id?: string | null // For ClientEmployee and Dependent
  parent_person_id?: string | null // DEPRECATED: For Dependent - use dependent_info instead
  family_id?: string | null
  dependent_info?: DependentInfo | null
  /** Inline to preserve backward compatibility: shared ContactInfo uses preferred_method: ContactMethod enum; PersonCreate keeps preferred_method?: string | null for form/API flexibility. */
  contact_info?: {
    email?: string | null
    phone?: string | null
    mobile?: string | null
    preferred_method?: string | null
  } | null
  address?: Address | null
  emergency_contact?: EmergencyContact | null
  employment_info?: EmploymentInfo | null
  license_info?: LicenseInfo | null
  staff_info?: StaffInfo | null
  secondary_roles?: PersonType[]
  metadata?: Record<string, unknown> | null
}

export interface AddSecondaryRoleRequest {
  person_type: PersonType
}

export interface PersonListParams extends ListParams {
  client_id?: string
  person_type?: PersonType
}

export const personsApi = {
  /**
   * Create a new person
   */
  async create(personData: PersonCreate): Promise<Person> {
    return apiClient.post<Person>('/persons', personData)
  },

  /**
   * Get person by ID
   */
  async getById(personId: string): Promise<Person> {
    return apiClient.get<Person>(`/persons/${personId}`)
  },

  /**
   * List persons
   */
  async list(params?: PersonListParams): Promise<PaginatedResponse<Person>> {
    return apiClient.get<PaginatedResponse<Person>>('/persons', params as Record<string, unknown>)
  },

  /**
   * Update person
   */
  async update(personId: string, data: Partial<PersonCreate>): Promise<Person> {
    return apiClient.patch<Person>(`/persons/${personId}`, data)
  },

  /**
   * Update employment info
   */
  async updateEmploymentInfo(personId: string, data: Partial<EmploymentInfo>): Promise<Person> {
    return apiClient.patch<Person>(`/persons/${personId}/employment-info`, data)
  },

  /**
   * Update dependent info
   */
  async updateDependentInfo(personId: string, data: Partial<DependentInfo>): Promise<Person> {
    return apiClient.patch<Person>(`/persons/${personId}/dependent-info`, data)
  },

  /**
   * Activate person
   */
  async activate(personId: string): Promise<Person> {
    return apiClient.post<Person>(`/persons/${personId}/activate`)
  },

  /**
   * Deactivate person
   */
  async deactivate(personId: string, reason?: string): Promise<Person> {
    return apiClient.post<Person>(`/persons/${personId}/deactivate`, reason != null ? { reason } : undefined)
  },

  /**
   * Terminate person (reason required)
   */
  async terminate(personId: string, reason: string): Promise<Person> {
    return apiClient.post<Person>(`/persons/${personId}/terminate`, { reason })
  },

  /**
   * Archive person
   */
  async archive(personId: string): Promise<Person> {
    return apiClient.post<Person>(`/persons/${personId}/archive`)
  },

  /**
   * Restore person from archive
   */
  async restore(personId: string): Promise<Person> {
    return apiClient.post<Person>(`/persons/${personId}/restore`)
  },

  /**
   * Add secondary role (dual-role person)
   */
  async addSecondaryRole(personId: string, data: AddSecondaryRoleRequest): Promise<Person> {
    return apiClient.post<Person>(`/persons/${personId}/secondary-roles`, data)
  },

  /**
   * Remove secondary role
   */
  async removeSecondaryRole(personId: string): Promise<Person> {
    return apiClient.delete<Person>(`/persons/${personId}/secondary-roles`)
  },

  /**
   * Update emergency contact
   */
  async updateEmergencyContact(personId: string, data: EmergencyContact): Promise<Person> {
    return apiClient.patch<Person>(`/persons/${personId}/emergency-contact`, data)
  },

  /**
   * Update license info
   */
  async updateLicenseInfo(personId: string, data: LicenseInfo): Promise<Person> {
    return apiClient.patch<Person>(`/persons/${personId}/license-info`, data)
  },

  /**
   * Update staff info
   */
  async updateStaffInfo(personId: string, data: StaffInfo): Promise<Person> {
    return apiClient.patch<Person>(`/persons/${personId}/staff-info`, data)
  },

  /**
   * Get person by user ID
   */
  async getByUserId(userId: string): Promise<Person> {
    return apiClient.get<Person>(`/persons/by-user/${userId}`)
  },

  /**
   * Get persons by type for a tenant
   */
  async getByType(tenantId: string, personType: PersonType): Promise<Person[]> {
    const res = await apiClient.get<Person[] | { items: Person[] }>(
      `/persons/by-type/${personType}`,
      { tenant_id: tenantId } as Record<string, unknown>
    )
    return Array.isArray(res) ? res : (res.items ?? [])
  },
}
