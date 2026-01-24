/**
 * Create Client Tag - redirects to Client Tags list (create via modal)
 */

import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/client-tags/new')({
  beforeLoad: () => {
    throw redirect({ to: '/client-tags' })
  },
  component: () => null,
})
