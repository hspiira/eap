/**
 * KPIs List Page
 * To be implemented in Phase 6.2
 */

import { createFileRoute } from '@tanstack/react-router'
import { AppLayout } from '@/components/layout/AppLayout'

export const Route = createFileRoute('/kpis/')({
  component: KPIsPage,
})

function KPIsPage() {
  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-safe mb-6">KPIs</h1>
        <p className="text-safe-light">KPI management will be implemented here.</p>
      </div>
    </AppLayout>
  )
}
