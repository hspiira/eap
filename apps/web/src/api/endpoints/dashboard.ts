/**
 * Dashboard aggregate API.
 *
 * One tenant-scoped read replacing the earlier fan-out of limit=1 list calls.
 * Tenant context is added by the API client from the current session.
 *
 * No fixture path. Every figure on the dashboard is a count the API computes,
 * so a local sample would put invented numbers behind real-looking charts.
 */

import type { DashboardResponse } from "@/api/generated"
import type { DashboardRange } from "@/lib/dashboard"
import type { RequestOptions } from "@/types/api"

import apiClient from "../client"

export const dashboardApi = {
  async get(range: DashboardRange, options?: RequestOptions): Promise<DashboardResponse> {
    return apiClient.get<DashboardResponse>(
      "/dashboard",
      { range: range.preset, start: range.start, end: range.end, year: range.year },
      options,
    )
  },
}
