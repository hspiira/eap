/**
 * Create Industry - redirects to Settings > Industries (create via modal)
 */

import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/industries/new')({
  beforeLoad: () => {
    throw redirect({ to: '/settings', search: { tab: 'industries' }, replace: true })
  },
  component: () => null,
})
