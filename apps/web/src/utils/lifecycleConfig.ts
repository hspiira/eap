/**
 * Allowed lifecycle actions per status. Used by LifecycleActions component.
 */

export type LifecycleAction =
  | 'activate'
  | 'deactivate'
  | 'suspend'
  | 'terminate'
  | 'archive'
  | 'restore'
  | 'renew'
  | 'verify'
  | 'ban'
  | 'complete'
  | 'cancel'
  | 'no-show'
  | 'reschedule'
  | 'publish'

const BASE_ACTIVE_ACTIONS: LifecycleAction[] = ['deactivate', 'archive']
const BASE_INACTIVE_ACTIONS: LifecycleAction[] = ['activate', 'archive']
const BASE_ARCHIVED_ACTIONS: LifecycleAction[] = ['restore']
const BASE_PENDING_ACTIONS: LifecycleAction[] = ['activate', 'archive']

export function getAllowedLifecycleActions(
  status: string,
  kind: 'base' | 'user' | 'tenant' | 'client' | 'contract' | 'service' | 'session' | 'document' = 'base'
): LifecycleAction[] {
  const s = status.toLowerCase()
  if (kind === 'user') {
    if (s === 'active') return ['suspend', 'ban', 'deactivate', 'terminate']
    if (s === 'suspended' || s === 'inactive') return ['activate']
    if (s === 'banned' || s === 'terminated') return []
    if (s === 'pending verification') return ['activate', 'suspend']
    return []
  }
  if (kind === 'tenant') {
    if (s === 'active') return ['suspend', 'terminate', 'archive']
    if (s === 'suspended') return ['activate', 'terminate', 'archive']
    if (s === 'archived') return ['restore']
    if (s === 'terminated') return []
    return []
  }
  if (kind === 'client' || kind === 'service' || kind === 'base') {
    if (s === 'active') return ['deactivate', 'archive']
    if (s === 'inactive') return ['activate', 'archive']
    if (s === 'archived') return ['restore']
    if (s === 'pending') return ['activate', 'archive']
    if (s === 'deleted' || s === 'terminated') return []
    return BASE_ACTIVE_ACTIONS
  }
  if (kind === 'contract') {
    if (s === 'active') return ['terminate', 'renew']
    if (s === 'pending' || s === 'draft') return ['activate', 'terminate']
    if (s === 'expired' || s === 'renewed') return ['renew']
    if (s === 'terminated') return []
    return []
  }
  if (kind === 'session') {
    if (s === 'scheduled' || s === 'rescheduled') return ['complete', 'cancel', 'no-show', 'reschedule']
    if (s === 'completed' || s === 'cancelled' || s === 'no show') return ['archive']
    if (s === 'archived') return ['restore']
    return []
  }
  if (kind === 'document') {
    if (s === 'draft') return ['publish', 'archive']
    if (s === 'published') return ['archive']
    if (s === 'archived') return ['restore']
    if (s === 'expired') return []
    return []
  }
  if (s === 'active') return BASE_ACTIVE_ACTIONS
  if (s === 'inactive' || s === 'pending') return BASE_INACTIVE_ACTIONS
  if (s === 'archived') return BASE_ARCHIVED_ACTIONS
  if (s === 'pending') return BASE_PENDING_ACTIONS
  return []
}
