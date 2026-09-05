import apiClient from "../client"
import type { Document, ListParams, PaginatedResponse } from "../types"

export const documentsApi = {
  async list(params?: ListParams & { client_id?: string }): Promise<PaginatedResponse<Document>> {
    return apiClient.get<PaginatedResponse<Document>>("/documents", params)
  },
}
