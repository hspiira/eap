/**
 * Dashboard Page
 * To be implemented in Phase 9.1
 */

import { createFileRoute } from '@tanstack/react-router'
import { AppLayout } from '@/components/layout/AppLayout'

export const Route = createFileRoute('/dashboard/')({
  component: DashboardPage,
})

function DashboardPage() {
  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-safe mb-6">Dashboard</h1>
        <p className="text-safe-light">Dashboard will be implemented here.</p>
      </div>
    </AppLayout>
  )
}
