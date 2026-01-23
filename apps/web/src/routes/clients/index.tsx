/**
 * Clients List Page
 * To be implemented in Phase 3.3
 */

import { createFileRoute } from '@tanstack/react-router'
import { AppLayout } from '@/components/layout/AppLayout'

export const Route = createFileRoute('/clients/')({
  component: ClientsPage,
})

function ClientsPage() {
  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-safe mb-6">Clients</h1>
        <p className="text-safe-light">Client management will be implemented here.</p>
      </div>
    </AppLayout>
  )
}
