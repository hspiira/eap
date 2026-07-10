/**
 * Feature flags for in-flight modules.
 *
 * Modules whose backend is not wired yet (or whose UI is a placeholder) hide
 * their sidebar entry by default. Flip to `true` once the route is real.
 *
 * Override per-environment via `VITE_FEATURE_<NAME>=true`.
 */

function envFlag(name: string, defaultValue: boolean): boolean {
  const raw = (import.meta.env as Record<string, string | undefined>)?.[`VITE_FEATURE_${name}`]
  if (raw === 'true') return true
  if (raw === 'false') return false
  return defaultValue
}

export const featureFlags = {
  contacts: envFlag('CONTACTS', false),
  audit: envFlag('AUDIT', false),
  activities: envFlag('ACTIVITIES', false),
  kpis: envFlag('KPIS', false),
  documents: envFlag('DOCUMENTS', false),
} as const

export type FeatureFlag = keyof typeof featureFlags
