/**
 * Create Session - redirects to Sessions list (create via modal)
 */

import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/sessions/new')({
  beforeLoad: () => {
    throw redirect({ to: '/sessions', replace: true })
  },
  component: () => null,
})
