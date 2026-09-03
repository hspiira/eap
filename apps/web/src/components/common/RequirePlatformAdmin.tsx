import { type ReactNode } from 'react'

import { ShieldAlert } from 'lucide-react'

import { RequireAuth } from '@/components/common/RequireAuth'
import { useTenantStore } from '@/store/slices/tenantSlice'

interface RequirePlatformAdminProps {
  redirectAfterLogin?: string
  children: ReactNode
}

function platformTenantId(): string {
  return (import.meta.env.VITE_PLATFORM_TENANT_ID ?? '').trim()
}

/**
 * Gate for platform-admin-only routes (tenants management, etc.).
 *
 * Wraps RequireAuth and additionally checks the current tenant matches the
 * configured PLATFORM_TENANT_ID. When the env var is empty (dev/single-tenant)
 * we skip the check entirely.
 */
export function RequirePlatformAdmin({
  redirectAfterLogin,
  children,
}: RequirePlatformAdminProps) {
  return (
    <RequireAuth redirectAfterLogin={redirectAfterLogin}>
      <PlatformGate>{children}</PlatformGate>
    </RequireAuth>
  )
}

function PlatformGate({ children }: { children: ReactNode }) {
  const currentTenantId = useTenantStore((s) => s.currentTenantId)
  const required = platformTenantId()

  if (required && currentTenantId !== required) {
    return <Forbidden />
  }

  return <>{children}</>
}

function Forbidden() {
  return (
    <div className="grid min-h-svh w-full place-items-center bg-bg p-6 text-fg">
      <div className="max-w-md space-y-3 text-center">
        <ShieldAlert className="mx-auto size-10 text-fg-muted" aria-hidden="true" />
        <h1 className="text-xl font-semibold">Platform admin only</h1>
        <p className="text-sm text-fg-muted">
          This area is restricted to Minet platform administrators. If you believe you
          should have access, contact your administrator.
        </p>
      </div>
    </div>
  )
}
