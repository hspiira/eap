/**
 * Create Service - redirects to Services list (create via modal)
 */

import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/services/new')({
  beforeLoad: () => {
    throw redirect({ to: '/services' })
  },
  component: () => null,
})
