/**
 * Diagnoses API.
 *
 * A two-level taxonomy: types → diagnoses. The rows are global so prevalence
 * stays comparable across tenants; taxonomy writes are platform-admin only.
 * Per-tenant preference lives in the overlay, which hides, reorders and
 * relabels without changing the shared row.
 *
 * Fixture is DEV-only and read-only.
 */

import type { Schemas } from "@/api/generated"
import { useFixtures } from "@/lib/fixtures"
import type { Diagnosis, DiagnosisTree, DiagnosisType } from "@/types/entities"

import apiClient from "../client"
import { fixtureGetTree, fixtureGetTypes, fixtureListDiagnoses } from "./diagnoses-fixture"

export interface DiagnosisListParams {
  type_code?: string
  active_only?: boolean
}

export type DiagnosisTypeCreate = Schemas["DiagnosisTypeCreate"]
export type DiagnosisTypeUpdate = Schemas["DiagnosisTypeUpdate"]
export type DiagnosisCreate = Schemas["DiagnosisCreate"]
export type DiagnosisUpdate = Schemas["DiagnosisUpdate"]
export type DiagnosisOverlay = Schemas["DiagnosisOverlayResponse"]
export type DiagnosisOverlayUpdate = Schemas["DiagnosisOverlayUpdate"]
export type DiagnosisCapabilities = Schemas["DiagnosisCapabilitiesResponse"]

export const diagnosesApi = {
  async getTypes(): Promise<DiagnosisType[]> {
    if (useFixtures()) return Promise.resolve(fixtureGetTypes())
    return apiClient.get<DiagnosisType[]>("/diagnoses/types")
  },

  async getTree(): Promise<DiagnosisTree> {
    if (useFixtures()) return Promise.resolve(fixtureGetTree())
    return apiClient.get<DiagnosisTree>("/diagnoses/tree")
  },

  async list(params: DiagnosisListParams = {}): Promise<Diagnosis[]> {
    if (useFixtures()) return Promise.resolve(fixtureListDiagnoses(params.type_code))
    return apiClient.get<Diagnosis[]>("/diagnoses", params)
  },

  async capabilities(): Promise<DiagnosisCapabilities> {
    if (useFixtures()) {
      return Promise.resolve({ can_manage_taxonomy: false, can_manage_overlay: true })
    }
    return apiClient.get<DiagnosisCapabilities>("/diagnoses/capabilities")
  },

  // Taxonomy writes: platform admin only, 403 otherwise.
  async createType(data: DiagnosisTypeCreate): Promise<DiagnosisType> {
    return apiClient.post<DiagnosisType>("/diagnoses/types", data)
  },

  async updateType(typeId: string, data: DiagnosisTypeUpdate): Promise<DiagnosisType> {
    return apiClient.patch<DiagnosisType>(`/diagnoses/types/${typeId}`, data)
  },

  async setTypeActive(typeId: string, isActive: boolean): Promise<DiagnosisType> {
    return apiClient.post<DiagnosisType>(
      `/diagnoses/types/${typeId}/active?is_active=${isActive}`,
      {},
    )
  },

  async createDiagnosis(data: DiagnosisCreate): Promise<Diagnosis> {
    return apiClient.post<Diagnosis>("/diagnoses", data)
  },

  async updateDiagnosis(diagnosisId: string, data: DiagnosisUpdate): Promise<Diagnosis> {
    return apiClient.patch<Diagnosis>(`/diagnoses/${diagnosisId}`, data)
  },

  async setDiagnosisActive(diagnosisId: string, isActive: boolean): Promise<Diagnosis> {
    return apiClient.post<Diagnosis>(`/diagnoses/${diagnosisId}/active?is_active=${isActive}`, {})
  },

  // Tenant overlay: tenant admin.
  async listOverlay(): Promise<DiagnosisOverlay[]> {
    if (useFixtures()) return Promise.resolve([])
    return apiClient.get<DiagnosisOverlay[]>("/diagnoses/settings")
  },

  async setOverlay(data: DiagnosisOverlayUpdate): Promise<DiagnosisOverlay> {
    return apiClient.put<DiagnosisOverlay>("/diagnoses/settings", data)
  },
}
