/**
 * Persons List (legacy)
 * Redirects to Roster. Use /people/client-people or /service-providers.
 */

import { createFileRoute, redirect } from '@tanstack/react-router'
import { requireAuthBeforeLoad } from '@/lib/route-auth'

export const Route = createFileRoute('/persons/')({
  beforeLoad: () => {
    requireAuthBeforeLoad()
    throw redirect({ to: '/people/client-people', replace: true })
  },
  component: () => null,
})
