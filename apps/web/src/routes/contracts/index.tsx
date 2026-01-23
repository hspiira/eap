/**
 * Contracts List Page
 * To be implemented in Phase 4.2
 */

import { createFileRoute } from '@tanstack/react-router'
import { AppLayout } from '@/components/layout/AppLayout'

export const Route = createFileRoute('/contracts/')({
  component: ContractsPage,
})

function ContractsPage() {
  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-safe mb-6">Contracts</h1>
        <p className="text-safe-light">Contract management will be implemented here.</p>
      </div>
    </AppLayout>
  )
}
