import { Outlet } from "@tanstack/react-router"
import type { ReactNode } from "react"

import { RequireAuth } from "@/components/common/RequireAuth"

export function AuthedLayout({ children }: { children?: ReactNode }) {
  return <RequireAuth>{children ?? <Outlet />}</RequireAuth>
}
