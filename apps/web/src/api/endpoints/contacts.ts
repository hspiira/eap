/**
 * Contacts API Endpoints
 */

import apiClient from '../client'
import type { Contact, PaginatedResponse, ListParams } from '../types'
import type { ContactInfo } from '@/types/entities'

export interface ContactCreate {
  client_id: string
  first_name: string
  last_name: string
  title?: string | null
  contact_info?: ContactInfo | null
  metadata?: Record<string, unknown> | null
}

export const contactsApi = {
  /**
   * Create a new contact
   */
  async create(contactData: ContactCreate): Promise<Contact> {
    return apiClient.post<Contact>('/contacts', contactData)
  },

  /**
   * Get contact by ID
   */
  async getById(contactId: string): Promise<Contact> {
    return apiClient.get<Contact>(`/contacts/${contactId}`)
  },

  /**
   * List contacts
   */
  async list(params?: ListParams): Promise<PaginatedResponse<Contact>> {
    return apiClient.get<PaginatedResponse<Contact>>('/contacts', params as Record<string, unknown>)
  },

  /**
   * Update contact
   */
  async update(contactId: string, data: Partial<ContactCreate>): Promise<Contact> {
    return apiClient.patch<Contact>(`/contacts/${contactId}`, data)
  },

  /**
   * Activate contact
   */
  async activate(contactId: string): Promise<Contact> {
    return apiClient.post<Contact>(`/contacts/${contactId}/activate`, {})
  },

  /**
   * Deactivate contact
   */
  async deactivate(contactId: string): Promise<Contact> {
    return apiClient.post<Contact>(`/contacts/${contactId}/deactivate`, {})
  },

  /**
   * Set contact as primary for client
   */
  async setPrimary(contactId: string): Promise<Contact> {
    return apiClient.post<Contact>(`/contacts/${contactId}/set-primary`, {})
  },

  /**
   * Get primary contact for a client
   */
  async getPrimaryForClient(clientId: string): Promise<Contact | null> {
    return apiClient.get<Contact | null>(`/contacts/client/${clientId}/primary`)
  },
}
