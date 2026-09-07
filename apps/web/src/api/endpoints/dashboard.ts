/**
 * Dashboard aggregate API.
 *
 * One tenant-scoped read replacing the earlier fan-out of limit=1 list calls.
 * Tenant context is added by the API client from the current session.
 */

import type { DashboardResponse } from "@/api/generated"
import { useFixtures } from "@/lib/fixtures"
import type { RequestOptions } from "@/types/api"

import apiClient from "../client"
import { fixtureDashboard } from "./dashboard-fixture"

export const dashboardApi = {
  async get(options?: RequestOptions): Promise<DashboardResponse> {
    if (useFixtures()) return Promise.resolve(fixtureDashboard())
    return apiClient.get<DashboardResponse>("/dashboard", undefined, options)
  },
}
