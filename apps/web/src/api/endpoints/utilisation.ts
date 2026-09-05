import type { UtilisationEvent } from "@/types/entities"

import apiClient from "../client"

export const utilisationApi = {
  async byContract(contractId: string): Promise<UtilisationEvent[]> {
    return apiClient.get<UtilisationEvent[]>(`/contracts/${contractId}/utilisation-events`)
  },
}
