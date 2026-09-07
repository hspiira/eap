/**
 * Global search API.
 *
 * One authenticated read over the record categories the header dialog offers.
 * Tenant context is added by the API client from the current session, so the
 * caller never names a tenant here.
 *
 * A POST that reads. The search term is user-entered text that routinely
 * names a person; in a query string it would be written to the server access
 * log and to every proxy log in front of it, so it travels in the body.
 */

import type { GlobalSearchResponse } from "@/api/generated"
import type { RequestOptions } from "@/types/api"

import apiClient from "../client"

/** Below this the dialog shows destinations only; the API agrees. */
export const MIN_SEARCH_LENGTH = 2

/** Per category, matching the API default. */
export const SEARCH_RESULT_LIMIT = 5

export interface GlobalSearchParams {
  q: string
  limit?: number
}

export const searchApi = {
  async global(
    params: GlobalSearchParams,
    options?: RequestOptions,
  ): Promise<GlobalSearchResponse> {
    return apiClient.post<GlobalSearchResponse>("/search", params, options)
  },
}
