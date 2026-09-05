import type { Schemas } from "@/api/generated"

import apiClient from "../client"
import type { Contact, ListParams, PaginatedResponse } from "../types"

export type ContactCreate = Schemas["ContactCreate"]
export type ContactUpdate = Schemas["ContactUpdate"]

export const contactsApi = {
  async create(data: ContactCreate): Promise<Contact> {
    return apiClient.post<Contact>("/contacts", data)
  },
  async update(contactId: string, data: ContactUpdate): Promise<Contact> {
    return apiClient.patch<Contact>(`/contacts/${contactId}`, data)
  },
  async list(
    params?: ListParams & { client_id?: string; is_primary?: boolean },
  ): Promise<PaginatedResponse<Contact>> {
    return apiClient.get<PaginatedResponse<Contact>>("/contacts", params)
  },
  async byClient(clientId: string): Promise<Contact[]> {
    const response = await apiClient.get<PaginatedResponse<Contact>>(`/contacts/client/${clientId}`)
    return response.items
  },
  async primary(clientId: string): Promise<Contact> {
    return apiClient.get<Contact>(`/contacts/client/${clientId}/primary`)
  },
}
