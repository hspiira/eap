/**
 * Create KPI - redirects to KPIs list (create via modal)
 */

import { createFileRoute, redirect } from '@tanstack/react-router'
import { requireAuthBeforeLoad } from '@/lib/route-auth'

export const Route = createFileRoute('/kpis/new')({
  beforeLoad: () => {
    requireAuthBeforeLoad()
    throw redirect({ to: '/kpis', replace: true })
  },
  component: () => null,
})
