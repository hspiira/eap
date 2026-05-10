/**
 * Persons API Endpoints
 *
 * **BE-canonical model.** Person is a thin link between a pre-existing User
 * and a Client (via employment_info) or a primary employee (via dependent_info).
 * The BE schema declares `additionalProperties: false` — first_name, last_name,
 * date_of_birth, gender, contact_info, address are NOT accepted.
 *
 * Person creation is a 2-step flow:
 *   1. POST /users      → returns user_id
 *   2. POST /persons    → with {person_type, user_id, tenant_id, employment_info? | dependent_info?, family_id?}
 *
 * Demographic display (name, contact) is sourced from the linked User's email
 * or from `employment_info.role` / `department`; the BE does not store names.
 */

import type {
  EmploymentInfoCreateSchema,
  PersonCreate,
} from '@/api/generated'
import type {
  DependentInfo,
  EmergencyContact,
  LicenseInfo,
  StaffInfo,
} from '@/types/entities'
import type { PersonType } from '@/types/enums'

import apiClient from '../client'
import type { ListParams, PaginatedResponse, Person } from '../types'

export type { EmploymentInfoCreateSchema, PersonCreate }

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
   * Update employment info. BE wraps the payload as `{employment_info: {...}}`.
   */
  async updateEmploymentInfo(
    personId: string,
    employment_info: EmploymentInfoCreateSchema,
  ): Promise<Person> {
    return apiClient.patch<Person>(`/persons/${personId}/employment-info`, {
      employment_info,
    })
  },

  /**
   * Update dependent info. BE wraps the payload as `{dependent_info: {...}}`.
   */
  async updateDependentInfo(
    personId: string,
    dependent_info: Partial<DependentInfo>,
  ): Promise<Person> {
    return apiClient.patch<Person>(`/persons/${personId}/dependent-info`, {
      dependent_info,
    })
  },

  /**
   * Activate person
   */
  async activate(personId: string): Promise<Person> {
    return apiClient.post<Person>(`/persons/${personId}/activate`)
  },

  /**
   * Deactivate person. BE `PersonDeactivateRequest` accepts `{reason?}`.
   */
  async deactivate(personId: string, reason?: string): Promise<Person> {
    return apiClient.post<Person>(`/persons/${personId}/deactivate`, reason ? { reason } : {})
  },

  /**
   * Terminate person. BE `PersonTerminateRequest` requires `{reason}`.
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
   * Add secondary role (dual-role person). BE route is singular `/secondary-role`.
   */
  async addSecondaryRole(personId: string, data: AddSecondaryRoleRequest): Promise<Person> {
    return apiClient.post<Person>(`/persons/${personId}/secondary-role`, data)
  },

  /**
   * Remove secondary role. BE route is singular `/secondary-role`.
   */
  async removeSecondaryRole(personId: string): Promise<Person> {
    return apiClient.delete<Person>(`/persons/${personId}/secondary-role`)
  },

  /**
   * Update emergency contact. BE wraps as `{emergency_contact: {...}}`.
   */
  async updateEmergencyContact(personId: string, emergency_contact: EmergencyContact): Promise<Person> {
    return apiClient.patch<Person>(`/persons/${personId}/emergency-contact`, {
      emergency_contact,
    })
  },

  /**
   * Update license info. BE wraps as `{license_info: {...}}`.
   */
  async updateLicenseInfo(personId: string, license_info: LicenseInfo): Promise<Person> {
    return apiClient.patch<Person>(`/persons/${personId}/license-info`, {
      license_info,
    })
  },

  /**
   * Update staff info. BE wraps as `{staff_info: {...}}`.
   */
  async updateStaffInfo(personId: string, staff_info: StaffInfo): Promise<Person> {
    return apiClient.patch<Person>(`/persons/${personId}/staff-info`, { staff_info })
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
