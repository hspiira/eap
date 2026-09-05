import apiClient from "../client"
import type { Document, ListParams, PaginatedResponse } from "../types"

export const documentsApi = {
  async list(params?: ListParams & { client_id?: string; contract_id?: string }): Promise<PaginatedResponse<Document>> {
    return apiClient.get<PaginatedResponse<Document>>("/documents", params)
  },
  async uploadContractAttachment(contractId: string, file: File): Promise<Document> {
    const body = new FormData()
    body.append("file", file)
    return apiClient.postFormData<Document>(`/documents/contracts/${contractId}/attachments`, body)
  },
  async download(id: string): Promise<Blob> {
    return apiClient.getBlob(`/documents/${id}/download`)
  },
}
