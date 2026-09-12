import { Outlet } from "@tanstack/react-router"
import type { ReactNode } from "react"

import { AppLayout } from "@/components/AppLayout"
import { RequireAuth } from "@/components/common/RequireAuth"

/**
 * The app chrome, behind sign-in.
 *
 * Every section layout used to inline its own gate, and all of them rendered
 * `null` for a signed-out user. That reads as a blank page rather than a
 * redirect, and it leaves the route reachable: signing out and pressing back,
 * or typing the URL, still resolved here. Going through `RequireAuth` sends
 * the user to sign-in and records where they were, so signing back in returns
 * them to it.
 */
export function AuthedLayout({ children }: { children?: ReactNode }) {
  return (
    <RequireAuth>
      <AppLayout>{children ?? <Outlet />}</AppLayout>
    </RequireAuth>
  )
}
