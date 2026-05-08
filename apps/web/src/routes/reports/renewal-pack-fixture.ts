/**
 * Fixture for the per-client renewal pack template.
 *
 * Replaced by a BE call (likely `GET /v1/reports/renewal-pack/:client_id`) once Phase 3
 * lands the reporting endpoints. The shape declared here is the assumed contract — keep
 * it in sync with the BE model when it ships.
 */

import { ClientTier } from "@/types/enums"

export interface SessionMonthBucket {
  month: string
  count: number
}

export interface DiagnosisPrevalenceRow {
  label: string
  count: number
}

export interface CareCallbackRow {
  outcome: string
  count: number
  share: number
}

export interface SatisfactionBucket {
  bucket: string
  count: number
}

export interface RenewalPackData {
  client: { id: string; name: string; tier: ClientTier }
  period: string
  activeEmployees: number
  sessionsByMonth: SessionMonthBucket[]
  diagnosisPrevalence: DiagnosisPrevalenceRow[]
  careCallbacks: CareCallbackRow[]
  satisfaction: SatisfactionBucket[]
}

export const renewalPackFixture: RenewalPackData = {
  client: { id: "fixture-stanbic", name: "Stanbic Bank Kenya", tier: ClientTier.A },
  period: "Jun 2025 – May 2026",
  activeEmployees: 1840,
  sessionsByMonth: [
    { month: "Jun 2025", count: 84 },
    { month: "Jul 2025", count: 102 },
    { month: "Aug 2025", count: 91 },
    { month: "Sep 2025", count: 110 },
    { month: "Oct 2025", count: 124 },
    { month: "Nov 2025", count: 98 },
    { month: "Dec 2025", count: 67 },
    { month: "Jan 2026", count: 132 },
    { month: "Feb 2026", count: 118 },
    { month: "Mar 2026", count: 121 },
    { month: "Apr 2026", count: 105 },
    { month: "May 2026", count: 88 },
  ],
  diagnosisPrevalence: [
    { label: "F32 — Depressive episode", count: 218 },
    { label: "F41 — Anxiety disorder", count: 196 },
    { label: "F43 — Adjustment / stress reactions", count: 142 },
    { label: "F10 — Alcohol-use disorder", count: 71 },
    { label: "Other / undiagnosed", count: 53 },
  ],
  careCallbacks: [
    { outcome: "No further intervention", count: 312, share: 64 },
    { outcome: "Recommended additional sessions", count: 96, share: 20 },
    { outcome: "Crisis flag — escalated", count: 18, share: 4 },
    { outcome: "No response", count: 60, share: 12 },
  ],
  satisfaction: [
    { bucket: "1", count: 4 },
    { bucket: "2", count: 11 },
    { bucket: "3", count: 67 },
    { bucket: "4", count: 198 },
    { bucket: "5", count: 312 },
  ],
}
