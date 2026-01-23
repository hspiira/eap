/**
 * Tenants API Endpoints
 * 
 * Endpoints:
 * - POST /tenants - Create tenant
 * - GET /tenants/{tenant_id} - Get tenant details
 * - PATCH /tenants/{tenant_id} - Update tenant
 * - POST /tenants/{tenant_id}/activate - Activate tenant
 * - POST /tenants/{tenant_id}/suspend - Suspend tenant
 * - POST /tenants/{tenant_id}/terminate - Terminate tenant
 * - POST /tenants/{tenant_id}/archive - Archive tenant
 * - POST /tenants/{tenant_id}/restore - Restore tenant
 * - GET /tenants - List tenants (with filtering)
 * 
 * To be implemented in Phase 3.1
 */

import apiClient from '../client'
import type { Tenant, PaginatedResponse, ListParams } from '../types'

// Placeholder - will be implemented in Phase 3.1
export const tenantsApi = {
  // Implementation coming in Phase 3.1
}
