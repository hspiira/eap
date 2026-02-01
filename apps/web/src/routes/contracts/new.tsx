/**
 * Create Contract - redirects to Contracts list (create via modal)
 */

import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/contracts/new')({
  beforeLoad: () => {
    throw redirect({ to: '/contracts', replace: true })
  },
  component: () => null,
})
