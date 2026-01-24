/**
 * State Management
 * Zustand store slices: auth, tenant, entity cache, UI.
 * Use hooks (useAuthStore, useTenantStore, etc.) in components.
 */

export { useAuthStore } from './slices/authSlice'
export type { AuthStore, AuthState, AuthActions } from './slices/authSlice'

export { useTenantStore } from './slices/tenantSlice'
export type { TenantStore, TenantState, TenantActions } from './slices/tenantSlice'

export { useEntityCacheStore } from './slices/entityCacheSlice'
export type {
  EntityCacheStore,
  EntityCacheState,
  EntityCacheActions,
} from './slices/entityCacheSlice'

export { useUIStore } from './slices/uiSlice'
export type { UIStore, UIState, UIActions } from './slices/uiSlice'
