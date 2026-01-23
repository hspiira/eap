/**
 * API Module
 * Central export for all API functionality
 */

export { default as apiClient } from './client'
export * from './types'

// Auth endpoints
export * from './endpoints/auth'

// Users endpoints
export * from './endpoints/users'

// Tenants endpoints
export * from './endpoints/tenants'

// Other endpoints will be exported here as they are implemented
// etc.
