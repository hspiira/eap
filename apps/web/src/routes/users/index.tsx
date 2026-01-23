/**
 * Users List Page
 * To be implemented in Phase 3.2
 */

import { createFileRoute } from '@tanstack/react-router'
import { AppLayout } from '@/components/layout/AppLayout'

export const Route = createFileRoute('/users/')({
  component: UsersPage,
})

function UsersPage() {
  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-safe mb-6">Users</h1>
        <p className="text-safe-light">User management will be implemented here.</p>
      </div>
    </AppLayout>
  )
}
