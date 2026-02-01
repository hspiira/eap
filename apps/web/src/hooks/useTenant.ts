/**
 * useTenant Hook
 * Access tenant context. Implemented here so TenantContext only exports
 * the provider (fixes Fast Refresh "incompatible export" warning).
 */

import { useContext } from 'react'
import { TenantContext } from '@/contexts/TenantContext'

export function useTenant() {
  const context = useContext(TenantContext)
  if (context === undefined) {
    throw new Error('useTenant must be used within a TenantProvider')
  }
  return context
}
