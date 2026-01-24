/**
 * Industries List - redirects to Settings > Industries (create via modal)
 */

import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/industries/')({
  beforeLoad: () => {
    throw redirect({ to: '/settings', search: { tab: 'industries' } })
  },
  component: () => null,
})
