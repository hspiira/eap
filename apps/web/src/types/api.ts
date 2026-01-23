/**
 * API Request/Response Types
 * Types for API communication
 */

import type { BaseEntity } from './entities'

/**
 * Standard API error response
 */
export interface ErrorResponse {
  error: string // Error code (e.g., "NOT_FOUND", "VALIDATION_ERROR")
  message: string // Human-readable message
  details?: Array<{
    field: string | null
    message: string
    code: string | null
  }>
  timestamp: string // ISO 8601 datetime
  path?: string // Request path
  request_id?: string // Request tracking ID
}

/**
 * Paginated response structure
 */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
  has_more: boolean
}

/**
 * Pagination parameters
 */
export interface PaginationParams {
  page?: number // Default: 1, min: 1
  limit?: number // Default: 20, min: 1, max: 100
  offset?: number // Alternative to page (calculated as (page - 1) * limit)
}

/**
 * Filtering parameters (common across endpoints)
 */
export interface FilterParams {
  search?: string // Text search
  status?: string // Status enum value
  sort_by?: string // Field name to sort by
  sort_desc?: boolean // Descending order
  date_from?: string // ISO 8601 date
  date_to?: string // ISO 8601 date
}

/**
 * Create request (generic, entities will extend this)
 */
export interface CreateRequest {
  tenant_id?: string // Usually passed as query param or header
}

/**
 * Update request (generic, entities will extend this)
 */
export interface UpdateRequest {
  // Partial update - fields are optional
}

/**
 * List request parameters
 */
export interface ListParams extends PaginationParams, FilterParams {
  tenant_id?: string // Required for multi-tenant endpoints
}

/**
 * API client configuration
 */
export interface ApiClientConfig {
  baseUrl: string
  timeout?: number
  retryAttempts?: number
  retryDelay?: number
}

/**
 * Request options
 */
export interface RequestOptions {
  headers?: Record<string, string>
  signal?: AbortSignal
  timeout?: number
}

/**
 * Authentication response
 */
export interface AuthResponse {
  access_token: string
  token_type: 'bearer'
  expires_in: number // seconds
}

/**
 * Login request
 */
export interface LoginRequest {
  email: string
  password: string
}

/**
 * Field-specific validation errors
 */
export interface FieldErrors {
  [field: string]: string
}

/**
 * API error with status code
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public code: string,
    public status: number,
    public fieldErrors?: FieldErrors
  ) {
    super(message)
    this.name = 'ApiError'
  }
}
