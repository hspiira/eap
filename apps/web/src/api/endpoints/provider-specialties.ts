/**
 * Provider specialties API.
 *
 * The catalogue is global and its writes are platform-only. A tenant selects
 * active entries by linking them to its own practitioners.
 *
 * A link to a retired specialty is retained and still returned, with
 * `specialty_is_active` false, so historical records keep their meaning. A
 * retired entry cannot be newly selected, and doing so is rejected.
 */

import apiClient from "../client"
import type { ProviderSpecialty, ProviderSpecialtyLink } from "@/types/entities"

export const providerSpecialtiesApi = {
  /** The global catalogue. Retired entries are excluded unless asked for. */
  async listCatalogue(includeInactive = false): Promise<ProviderSpecialty[]> {
    return apiClient.get<ProviderSpecialty[]>("/provider-specialties", {
      include_inactive: includeInactive,
    })
  },

  async listLinks(providerId: string): Promise<ProviderSpecialtyLink[]> {
    return apiClient.get<ProviderSpecialtyLink[]>("/provider-specialties/links", {
      provider_id: providerId,
    })
  },

  async link(providerId: string, specialtyId: string): Promise<ProviderSpecialtyLink> {
    return apiClient.post<ProviderSpecialtyLink>("/provider-specialties/links", {
      provider_id: providerId,
      specialty_id: specialtyId,
    })
  },

  async unlink(linkId: string): Promise<void> {
    await apiClient.delete(`/provider-specialties/links/${linkId}`)
  },
}
