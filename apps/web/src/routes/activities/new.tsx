/**
 * Create Activity - redirects to Activities list (create via modal)
 */

import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/activities/new')({
  beforeLoad: () => {
    throw redirect({ to: '/activities' })
  },
  component: () => null,
})
