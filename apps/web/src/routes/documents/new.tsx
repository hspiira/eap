/**
 * Create Document - redirects to Documents list (create via modal)
 */

import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/documents/new')({
  beforeLoad: () => {
    throw redirect({ to: '/documents', replace: true })
  },
  component: () => null,
})
