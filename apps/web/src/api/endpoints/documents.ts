/**
 * Documents API Endpoints
 */

import apiClient from '../client'
import type { Document, PaginatedResponse, ListParams } from '../types'
import type { DocumentType, DocumentStatus } from '@/types/enums'

export interface DocumentCreate {
  name: string
  document_type: DocumentType
  file?: File | null
  confidentiality_level?: string | null
  expiry_date?: string | null
  metadata?: Record<string, unknown> | null
}

export interface DocumentVersionCreate {
  file: File
  notes?: string | null
}

export interface ConfidentialityUpdate {
  confidentiality_level: string
}

export interface ExpiryUpdate {
  expiry_date: string | null
}

export const documentsApi = {
  /**
   * Create a new document
   */
  async create(documentData: DocumentCreate): Promise<Document> {
    const formData = new FormData()
    formData.append('name', documentData.name)
    formData.append('document_type', documentData.document_type)
    if (documentData.file) {
      formData.append('file', documentData.file)
    }
    if (documentData.confidentiality_level) {
      formData.append('confidentiality_level', documentData.confidentiality_level)
    }
    if (documentData.expiry_date) {
      formData.append('expiry_date', documentData.expiry_date)
    }
    if (documentData.metadata) {
      formData.append('metadata', JSON.stringify(documentData.metadata))
    }

    return apiClient.postFormData<Document>('/documents', formData)
  },

  /**
   * Get document by ID
   */
  async getById(documentId: string): Promise<Document> {
    return apiClient.get<Document>(`/documents/${documentId}`)
  },

  /**
   * List documents
   */
  async list(params?: ListParams): Promise<PaginatedResponse<Document>> {
    return apiClient.get<PaginatedResponse<Document>>('/documents', params as Record<string, unknown>)
  },

  /**
   * Update document metadata
   */
  async update(documentId: string, data: Partial<Omit<DocumentCreate, 'file'>>): Promise<Document> {
    return apiClient.patch<Document>(`/documents/${documentId}`, data)
  },

  /**
   * Publish document
   */
  async publish(documentId: string): Promise<Document> {
    return apiClient.post<Document>(`/documents/${documentId}/publish`, {})
  },

  /**
   * Create new version
   */
  async createVersion(documentId: string, versionData: DocumentVersionCreate): Promise<Document> {
    const formData = new FormData()
    formData.append('file', versionData.file)
    if (versionData.notes) {
      formData.append('notes', versionData.notes)
    }

    return apiClient.postFormData<Document>(
      `/documents/${documentId}/version`,
      formData
    )
  },

  /**
   * Get all versions
   */
  async getVersions(documentId: string): Promise<Document[]> {
    return apiClient.get<Document[]>(`/documents/${documentId}/versions`)
  },

  /**
   * Get latest version
   */
  async getLatest(documentId: string): Promise<Document> {
    return apiClient.get<Document>(`/documents/${documentId}/latest`)
  },

  /**
   * Set confidentiality level
   */
  async setConfidentiality(documentId: string, data: ConfidentialityUpdate): Promise<Document> {
    return apiClient.patch<Document>(`/documents/${documentId}/confidentiality`, data)
  },

  /**
   * Set expiry date
   */
  async setExpiry(documentId: string, data: ExpiryUpdate): Promise<Document> {
    return apiClient.patch<Document>(`/documents/${documentId}/expiry`, data)
  },

  /**
   * Archive document
   */
  async archive(documentId: string): Promise<Document> {
    return apiClient.post<Document>(`/documents/${documentId}/archive`, {})
  },

  /**
   * Download document file
   */
  async download(documentId: string): Promise<Blob> {
    return apiClient.getBlob(`/documents/${documentId}/download`)
  },
}
