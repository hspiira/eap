/**
 * Auth Layout
 * Shared layout for authentication pages (login, signup)
 */

import { createFileRoute, Outlet } from '@tanstack/react-router'

export const Route = createFileRoute('/auth')({
  component: AuthLayout,
})

function AuthLayout() {
  return (
    <div className="min-h-svh flex items-center justify-center px-4 bg-bg text-fg">
      <div className="w-full max-w-md py-8">
        <Outlet />
      </div>
    </div>
  )
}
