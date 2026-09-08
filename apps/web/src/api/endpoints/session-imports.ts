/**
 * Staged historical session import.
 *
 * Staging writes no sessions. It judges every row of an extract against the
 * reference data the environment holds right now and records an outcome per
 * row, so what an import would do is visible before anything is written.
 * Applying writes only the rows that came out Accepted.
 *
 * Staging the same file again is how rows re-judge once the reference data
 * improves: rows an earlier batch imported come back Duplicate, and the rest
 * are judged afresh. A batch still awaiting a decision holds its file, so
 * abandon it first.
 */

import type { components } from "@/api/generated/schema"

import apiClient from "../client"
import type { PaginatedResponse } from "../types"

export type SessionImportBatch = components["schemas"]["SessionImportBatchResponse"]
export type SessionImportRow = components["schemas"]["SessionImportRowPreview"]
export type SessionImportApplyResult = components["schemas"]["SessionImportApplyResponse"]
export type SessionImportOutcome = SessionImportRow["outcome"]

export interface SessionImportRowParams {
  outcome?: SessionImportOutcome
  page?: number
  limit?: number
}

export const sessionImportsApi = {
  /**
   * Judge an extract without writing anything.
   *
   * `sourceRecordKeyField` names a column holding a stable id for the source
   * row. The server refuses one that repeats or is blank anywhere, because a
   * key that fails open would stage a row as a silent duplicate; leave it unset
   * and rows are keyed by file and row number instead.
   */
  async stage(
    file: File,
    sourceSystem: string,
    sourceRecordKeyField?: string,
  ): Promise<SessionImportBatch> {
    const body = new FormData()
    body.append("file", file)
    const params = new URLSearchParams({ source_system: sourceSystem })
    if (sourceRecordKeyField) params.set("source_record_key_field", sourceRecordKeyField)
    return apiClient.postFormData<SessionImportBatch>(`/session-imports?${params}`, body)
  },

  async getBatch(batchId: string): Promise<SessionImportBatch> {
    return apiClient.get<SessionImportBatch>(`/session-imports/${batchId}`)
  },

  async listRows(
    batchId: string,
    params: SessionImportRowParams = {},
  ): Promise<PaginatedResponse<SessionImportRow>> {
    return apiClient.get<PaginatedResponse<SessionImportRow>>(
      `/session-imports/${batchId}/rows`,
      params,
    )
  },

  async apply(batchId: string): Promise<SessionImportApplyResult> {
    return apiClient.post<SessionImportApplyResult>(`/session-imports/${batchId}/apply`)
  },

  /** Close a batch nobody will apply. The reason goes on the record. */
  async abandon(batchId: string, reason: string): Promise<SessionImportBatch> {
    return apiClient.post<SessionImportBatch>(`/session-imports/${batchId}/abandon`, { reason })
  },
}
