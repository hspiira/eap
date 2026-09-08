/** Immutable record of one action. Mirrors BE `AuditLogResponse`. */
export interface AuditLog {
  id: string
  tenant_id?: string | null
  user_id?: string | null
  action_type: string
  resource_type: string
  resource_id?: string | null
  description?: string | null
  ip_address?: string | null
  user_agent?: string | null
  /** When the action happened. The API does not return a `created_at`. */
  occurred_at: string
  metadata?: Record<string, unknown> | null
}

/** One field's before and after. Mirrors BE `FieldChangeSchema`. */
export interface FieldChange {
  field_name: string
  old_value?: string | null
  new_value?: string | null
}

/**
 * The fields one audited action touched. Mirrors BE `EntityChangeResponse`.
 *
 * Carries no timestamp of its own: it is joined to its `audit_log_id` for that.
 * Values arrive already redacted for clinical resources.
 */
export interface EntityChange {
  id: string
  audit_log_id: string
  entity_type: string
  entity_id: string
  field_changes: FieldChange[]
}
