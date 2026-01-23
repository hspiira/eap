/**
 * Audit Logs Page
 * To be implemented in Phase 7.3
 */

import { createFileRoute } from '@tanstack/react-router'
import { AppLayout } from '@/components/layout/AppLayout'

export const Route = createFileRoute('/audit/')({
  component: AuditPage,
})

function AuditPage() {
  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-safe mb-6">Audit Logs</h1>
        <p className="text-safe-light">Audit log viewing will be implemented here.</p>
      </div>
    </AppLayout>
  )
}
