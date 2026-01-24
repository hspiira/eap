/**
 * Persons List (legacy)
 * Redirects to Client people. Use /people/client-people or /service-providers.
 */

import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/persons/')({
  beforeLoad: () => {
    throw redirect({ to: '/people/client-people' })
  },
  component: () => null,
})
