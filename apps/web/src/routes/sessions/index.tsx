/**
 * Sessions List Page
 * To be implemented in Phase 5.1
 */

import { createFileRoute } from '@tanstack/react-router'
import { AppLayout } from '@/components/layout/AppLayout'

export const Route = createFileRoute('/sessions/')({
  component: SessionsPage,
})

function SessionsPage() {
  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-safe mb-6">Service Sessions</h1>
        <p className="text-safe-light">Session management will be implemented here.</p>
      </div>
    </AppLayout>
  )
}
