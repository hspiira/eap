import { type ReactNode } from 'react'

import { ShieldAlert } from 'lucide-react'

import { RequireAuth } from '@/components/common/RequireAuth'
import { useHasClinicalScope } from '@/hooks/useCanWrite'

interface RequireClinicalScopeProps {
  redirectAfterLogin?: string
  children: ReactNode
}

/**
 * Gate for clinical (PHI) routes — cases, clinical notes, authorizations.
 * The BE fails closed on the same check (require_clinical_scope); this just
 * gives an unscoped session a clear message instead of a raw 403 from the API.
 */
export function RequireClinicalScope({
  redirectAfterLogin,
  children,
}: RequireClinicalScopeProps) {
  return (
    <RequireAuth redirectAfterLogin={redirectAfterLogin}>
      <ClinicalGate>{children}</ClinicalGate>
    </RequireAuth>
  )
}

function ClinicalGate({ children }: { children: ReactNode }) {
  const { hasScope, isLoading } = useHasClinicalScope()

  if (isLoading) return null
  if (!hasScope) return <Forbidden />

  return <>{children}</>
}

function Forbidden() {
  return (
    <div className="grid min-h-svh w-full place-items-center bg-bg p-6 text-fg">
      <div className="max-w-md space-y-3 text-center">
        <ShieldAlert className="mx-auto size-10 text-fg-muted" aria-hidden="true" />
        <h1 className="text-xl font-semibold">Clinical access required</h1>
        <p className="text-sm text-fg-muted">
          This area holds clinical records and is restricted to counsellors granted
          clinical access. Contact a platform admin if you believe you should have access.
        </p>
      </div>
    </div>
  )
}
