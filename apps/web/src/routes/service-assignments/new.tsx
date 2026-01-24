/**
 * Create Service Assignment - redirects to Service Assignments list (create via modal)
 */

import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/service-assignments/new')({
  beforeLoad: () => {
    throw redirect({ to: '/service-assignments' })
  },
  component: () => null,
})
