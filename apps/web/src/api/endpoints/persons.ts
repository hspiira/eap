/**
 * Persons API Endpoints
 */

import apiClient from '../client'
import type { Person, PaginatedResponse, ListParams } from '../types'
import type { PersonType } from '@/types/enums'

export interface PersonCreate {
  first_name: string
  last_name: string
  middle_name?: string | null
  person_type: PersonType
  date_of_birth?: string | null
  gender?: string | null
  client_id?: string | null // For ClientEmployee and Dependent
  parent_person_id?: string | null // For Dependent
  contact_info?: {
    email?: string | null
    phone?: string | null
    mobile?: string | null
    preferred_method?: string | null
  } | null
  address?: {
    street?: string | null
    city?: string | null
    state?: string | null
    postal_code?: string | null
    country?: string | null
  } | null
  emergency_contact?: {
    name?: string | null
    relationship?: string | null
    phone?: string | null
  } | null
  employment_info?: {
    employee_id?: string | null
    department?: string | null
    position?: string | null
    hire_date?: string | null
    work_status?: string | null
  } | null
  license_info?: {
    license_number?: string | null
    license_type?: string | null
    issuing_authority?: string | null
    issue_date?: string | null
    expiry_date?: string | null
  } | null
  staff_info?: {
    role?: string | null
    department?: string | null
  } | null
  secondary_roles?: PersonType[]
  metadata?: Record<string, unknown> | null
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
  async list(params?: ListParams): Promise<PaginatedResponse<Person>> {
    return apiClient.get<PaginatedResponse<Person>>('/persons', params as Record<string, unknown>)
  },

  /**
   * Update person
   */
  async update(personId: string, data: Partial<PersonCreate>): Promise<Person> {
    return apiClient.patch<Person>(`/persons/${personId}`, data)
  },
}
