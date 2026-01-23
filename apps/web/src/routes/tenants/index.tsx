/**
 * Tenants List Page
 * To be implemented in Phase 3.1
 */

import { createFileRoute } from '@tanstack/react-router'
import { AppLayout } from '@/components/layout/AppLayout'

export const Route = createFileRoute('/tenants/')({
  component: TenantsPage,
})

function TenantsPage() {
  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-safe mb-6">Tenants</h1>
        <p className="text-safe-light">Tenant management will be implemented here.</p>
      </div>
    </AppLayout>
  )
}
