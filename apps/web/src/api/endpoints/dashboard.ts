/**
 * Dashboard aggregate API.
 *
 * One tenant-scoped read replacing the earlier fan-out of limit=1 list calls.
 * Tenant context is added by the API client from the current session.
 */

import type { DashboardResponse } from "@/api/generated"
import type { DashboardRange } from "@/lib/dashboard"
import { useFixtures } from "@/lib/fixtures"
import type { RequestOptions } from "@/types/api"

import apiClient from "../client"
import { fixtureDashboard } from "./dashboard-fixture"

export const dashboardApi = {
  async get(range: DashboardRange, options?: RequestOptions): Promise<DashboardResponse> {
    if (useFixtures()) return Promise.resolve(fixtureDashboard(range))
    return apiClient.get<DashboardResponse>(
      "/dashboard",
      { range: range.preset, start: range.start, end: range.end },
      options,
    )
  },
}
