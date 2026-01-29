/**
 * Create KPI - redirects to KPIs list (create via modal)
 */

import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/kpis/new')({
  beforeLoad: () => {
    throw redirect({ to: '/kpis', replace: true })
  },
  component: () => null,
})
