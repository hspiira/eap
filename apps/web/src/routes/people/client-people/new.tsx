/**
 * Add Person to Roster (standalone page)
 * For direct URL access. Primary flow is via CreatePersonModal on roster and client detail.
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { AppLayout } from '@/components/layout/AppLayout'
import { CreatePersonForm } from '@/components/forms/CreatePersonForm'
import { ArrowLeft } from 'lucide-react'

export const Route = createFileRoute('/people/client-people/new')({
  validateSearch: (search: Record<string, unknown>) => ({
    client_id: typeof search?.client_id === 'string' ? search.client_id : undefined,
  }),
  component: CreateClientPersonPage,
})

function CreateClientPersonPage() {
  const navigate = useNavigate()
  const { client_id: initialClientId } = Route.useSearch()

  return (
    <AppLayout>
      <div className="max-w-2xl mx-auto">
        <button
          onClick={() => navigate({ to: '/people/client-people' })}
          className="flex items-center gap-2 text-text hover:text-primary mb-6 transition-colors"
        >
          <ArrowLeft size={18} />
          <span>Back to Roster</span>
        </button>

        <h1 className="text-3xl font-bold text-text mb-6">Add person to roster</h1>

        <div className="bg-surface border border-[0.5px] border-border p-6">
          <CreatePersonForm
            initialClientId={initialClientId}
            onSuccess={() => navigate({ to: '/people/client-people' })}
            onCancel={() => navigate({ to: '/people/client-people' })}
          />
        </div>
      </div>
    </AppLayout>
  )
}
