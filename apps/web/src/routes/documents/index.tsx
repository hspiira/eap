/**
 * Documents List Page
 * To be implemented in Phase 6.1
 */

import { createFileRoute } from '@tanstack/react-router'
import { AppLayout } from '@/components/layout/AppLayout'

export const Route = createFileRoute('/documents/')({
  component: DocumentsPage,
})

function DocumentsPage() {
  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-safe mb-6">Documents</h1>
        <p className="text-safe-light">Document management will be implemented here.</p>
      </div>
    </AppLayout>
  )
}
