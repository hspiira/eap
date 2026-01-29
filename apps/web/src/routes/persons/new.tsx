/**
 * Create Person (legacy)
 * Redirects to Roster create. Use /people/client-people/new or /service-providers/new.
 */

import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/persons/new')({
  beforeLoad: () => {
    throw redirect({ to: '/people/client-people/new', replace: true })
  },
  component: () => null,
})
