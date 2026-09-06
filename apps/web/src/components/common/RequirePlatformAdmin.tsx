import { type ReactNode } from "react"

import { ShieldAlert } from "lucide-react"

import { RequireAuth } from "@/components/common/RequireAuth"
import { useIsPlatformAdmin } from "@/hooks/useCanWrite"

interface RequirePlatformAdminProps {
  redirectAfterLogin?: string
  children: ReactNode
}

/**
 * Gate for platform-admin-only routes (tenants management, etc.).
 *
 * Wraps RequireAuth and asks the API who the caller is, rather than comparing
 * the current tenant against VITE_PLATFORM_TENANT_ID. The old check skipped
 * itself when that variable was empty, so every tenant saw the surface and
 * then got a 403 from an API that fails closed. One source of truth, and it
 * is the one that actually enforces.
 */
export function RequirePlatformAdmin({ redirectAfterLogin, children }: RequirePlatformAdminProps) {
  return (
    <RequireAuth redirectAfterLogin={redirectAfterLogin}>
      <PlatformGate>{children}</PlatformGate>
    </RequireAuth>
  )
}

function PlatformGate({ children }: { children: ReactNode }) {
  const { isPlatformAdmin, isLoading } = useIsPlatformAdmin()

  // Do not flash the forbidden screen before the answer arrives.
  if (isLoading) return null
  if (!isPlatformAdmin) return <Forbidden />

  return <>{children}</>
}

function Forbidden() {
  return (
    <div className="grid min-h-svh w-full place-items-center bg-bg p-6 text-fg">
      <div className="max-w-md space-y-3 text-center">
        <ShieldAlert className="mx-auto size-10 text-fg-muted" aria-hidden="true" />
        <h1 className="text-xl font-semibold">Platform admin only</h1>
        <p className="text-sm text-fg-muted">
          This area is restricted to Minet platform administrators. If you believe you should have
          access, contact your administrator.
        </p>
      </div>
    </div>
  )
}
