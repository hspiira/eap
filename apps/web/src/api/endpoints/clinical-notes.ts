/**
 * Clinical Notes API Endpoints
 *
 * `body` is a generic dict on the wire — the BE discriminates its required
 * shape by `note_type` server-side (see ClinicalNoteType in types/enums and
 * the DAP/SOAP/Narrative body interfaces in types/entities/clinical.ts).
 * A malformed body is rejected as a domain error, not a 422, so client-side
 * validation before submit matters.
 */

import type { Schemas } from '@/api/generated'

import apiClient from '../client'
import type { ClinicalNote } from '../types'

export type CreateClinicalNoteRequest = Schemas['CreateClinicalNoteRequest']
export type UpdateClinicalNoteBodyRequest = Schemas['UpdateClinicalNoteBodyRequest']
export type AmendClinicalNoteRequest = Schemas['AmendClinicalNoteRequest']

export const clinicalNotesApi = {
  async create(data: CreateClinicalNoteRequest): Promise<ClinicalNote> {
    return apiClient.post<ClinicalNote>('/clinical-notes', data)
  },

  async listForCase(caseId: string): Promise<ClinicalNote[]> {
    return apiClient.get<ClinicalNote[]>(`/cases/${caseId}/clinical-notes`)
  },

  async updateBody(noteId: string, data: UpdateClinicalNoteBodyRequest): Promise<ClinicalNote> {
    return apiClient.patch<ClinicalNote>(`/clinical-notes/${noteId}`, data)
  },

  async sign(noteId: string): Promise<ClinicalNote> {
    return apiClient.post<ClinicalNote>(`/clinical-notes/${noteId}/sign`, {})
  },

  async amend(noteId: string, data: AmendClinicalNoteRequest): Promise<ClinicalNote> {
    return apiClient.post<ClinicalNote>(`/clinical-notes/${noteId}/amend`, data)
  },
}
