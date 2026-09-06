/**
 * Feature flags for in-flight modules.
 *
 * Nav entries reference a flag one of two ways. `flag` hides the entry
 * entirely; `comingSoon` leaves it visible but greyed out and non-navigable.
 * Either way, flip the flag to `true` once the module is ready.
 *
 * Override per-environment via `VITE_FEATURE_<NAME>=true`.
 */

function envFlag(name: string, defaultValue: boolean): boolean {
  const raw = (import.meta.env as Record<string, string | undefined>)?.[`VITE_FEATURE_${name}`]
  if (raw === "true") return true
  if (raw === "false") return false
  return defaultValue
}

export const featureFlags = {
  contacts: envFlag("CONTACTS", false),
  audit: envFlag("AUDIT", false),
  activities: envFlag("ACTIVITIES", false),
  kpis: envFlag("KPIS", false),
  documents: envFlag("DOCUMENTS", false),
  surveys: envFlag("SURVEYS", false),
  campaigns: envFlag("CAMPAIGNS", false),
  worklist: envFlag("WORKLIST", false),
  engagements: envFlag("ENGAGEMENTS", false),
} as const

export type FeatureFlag = keyof typeof featureFlags
