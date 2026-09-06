/**
 * Provider specialties API.
 *
 * The catalogue is global and its writes are platform-only. A tenant selects
 * active entries by linking them to its own practitioners. A link to a
 * retired specialty is retained and still returned on read, but a retired
 * entry cannot be newly selected.
 */

import type { ProviderSpecialty } from "@/types/entities"

import apiClient from "../client"

export const providerSpecialtiesApi = {
  async list(): Promise<ProviderSpecialty[]> {
    return apiClient.get<ProviderSpecialty[]>("/provider-specialties")
  },

  async link(providerId: string, specialtyId: string): Promise<void> {
    await apiClient.post("/provider-specialties/links", {
      provider_id: providerId,
      specialty_id: specialtyId,
    })
  },

  async unlink(linkId: string): Promise<void> {
    await apiClient.delete(`/provider-specialties/links/${linkId}`)
  },
}
