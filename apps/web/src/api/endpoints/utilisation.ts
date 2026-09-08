import type { PaginationParams } from "@/api/types"
import type { UtilisationEvent } from "@/types/entities"

import apiClient from "../client"
import type { PaginatedResponse } from "../types"

export const utilisationApi = {
  async byContract(contractId: string): Promise<UtilisationEvent[]> {
    return apiClient.get<UtilisationEvent[]>(`/contracts/${contractId}/utilisation-events`)
  },

  async byClient(
    clientId: string,
    params?: PaginationParams,
  ): Promise<PaginatedResponse<UtilisationEvent>> {
    return apiClient.get<PaginatedResponse<UtilisationEvent>>(
      `/clients/${clientId}/utilisation-events`,
      params,
    )
  },
}
