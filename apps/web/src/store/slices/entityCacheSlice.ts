/**
 * Entity cache store slice
 * Normalized entity caches by type and id for optimistic updates
 * and to avoid redundant fetches.
 */

import { create } from 'zustand'

type EntityType = string
type EntityId = string

export interface EntityCacheState {
  /** Map of entityType -> id -> entity */
  cache: Record<EntityType, Record<EntityId, unknown>>
}

export interface EntityCacheActions {
  set: <T>(entityType: EntityType, id: EntityId, entity: T) => void
  setMany: <T>(entityType: EntityType, entities: T[], getKey?: (e: T) => string) => void
  get: <T>(entityType: EntityType, id: EntityId) => T | undefined
  invalidate: (entityType: EntityType, id?: EntityId) => void
  invalidateAll: () => void
}

export type EntityCacheStore = EntityCacheState & EntityCacheActions

export const useEntityCacheStore = create<EntityCacheStore>((set, get) => ({
  cache: {},

  set: (entityType, id, entity) =>
    set((state) => ({
      cache: {
        ...state.cache,
        [entityType]: {
          ...(state.cache[entityType] ?? {}),
          [id]: entity,
        },
      },
    })),

  setMany: (entityType, entities, getKey = (e: unknown) => (e as { id: string }).id) =>
    set((state) => {
      const next: Record<string, unknown> = { ...(state.cache[entityType] ?? {}) }
      for (const e of entities) {
        const k = getKey(e)
        if (k) next[k] = e
      }
      return {
        cache: {
          ...state.cache,
          [entityType]: next,
        },
      }
    }),

  get: (entityType, id) => {
    const byType = get().cache[entityType]
    if (!byType) return undefined
    return byType[id] as unknown
  },

  invalidate: (entityType, id) =>
    set((state) => {
      if (!id) {
        const { [entityType]: _, ...rest } = state.cache
        return { cache: rest }
      }
      const byType = state.cache[entityType]
      if (!byType) return state
      const { [id]: __, ...rest } = byType
      if (!Object.keys(rest).length) {
        const { [entityType]: ___, ...restCache } = state.cache
        return { cache: restCache }
      }
      return {
        cache: { ...state.cache, [entityType]: rest },
      }
    }),

  invalidateAll: () => set({ cache: {} }),
}))
