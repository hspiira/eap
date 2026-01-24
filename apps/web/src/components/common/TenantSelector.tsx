/**
 * Tenant Selector Component
 * Allows users to switch between available tenants
 */

import { useTenant } from '@/hooks/useTenant'
import type { Tenant } from '@/api/endpoints/tenants'

export function TenantSelector() {
  const { currentTenant, availableTenants, setCurrentTenant, isLoading } = useTenant()

  if (isLoading || availableTenants.length <= 1) {
    return null
  }

  const handleTenantChange = (tenantId: string) => {
    const tenant = availableTenants.find((t) => t.id === tenantId)
    if (tenant) {
      setCurrentTenant(tenant)
    }
  }

  return (
    <div className="mb-4">
      <label htmlFor="tenant-select" className="block text-safe text-sm font-medium mb-2">
        Current Tenant
      </label>
      <select
        id="tenant-select"
        value={currentTenant?.id || ''}
        onChange={(e) => handleTenantChange(e.target.value)}
        className="w-full px-4 py-2 bg-calm border-[0.5px] border-safe rounded-none focus:outline-none focus:border-natural"
      >
        {availableTenants.map((tenant) => (
          <option key={tenant.id} value={tenant.id}>
            {tenant.name}
          </option>
        ))}
      </select>
    </div>
  )
}
