/**
 * Audit Log
 */
export interface AuditLog {
  id: string
  tenant_id?: string | null
  user_id?: string | null
  action_type: string
  resource_type: string
  resource_id: string
  changes?: Record<string, unknown> | null
  ip_address?: string | null
  user_agent?: string | null
  created_at: string
}
