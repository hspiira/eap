/**
 * State Management
 * Zustand store slices: auth, tenant, entity cache, UI.
 * Use hooks (useAuthStore, useTenantStore, etc.) in components.
 */

export type { AuthActions,AuthState, AuthStore } from './slices/authSlice'
export { useAuthStore } from './slices/authSlice'
export type {
  EntityCacheActions,
  EntityCacheState,
  EntityCacheStore,
} from './slices/entityCacheSlice'
export { useEntityCacheStore } from './slices/entityCacheSlice'
export type { TenantActions,TenantState, TenantStore } from './slices/tenantSlice'
export { useTenantStore } from './slices/tenantSlice'
export type { UIActions,UIState, UIStore } from './slices/uiSlice'
export { useUIStore } from './slices/uiSlice'
