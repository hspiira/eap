import { useRouterState } from "@tanstack/react-router"
import type { ReactNode } from "react"

import { AppLayout } from "@/components/AppLayout"
import { useAuthStore } from "@/store/slices/authSlice"

export function PersistentAppLayout({ children }: { children: ReactNode }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const publicPage = useRouterState({
    select: (state) =>
      state.location.pathname === "/auth" ||
      state.location.pathname.startsWith("/auth/") ||
      state.location.pathname === "/design",
  })

  if (!isAuthenticated || publicPage) return children
  return <AppLayout>{children}</AppLayout>
}
