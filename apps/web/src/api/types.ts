/**
 * API-specific type definitions
 * Re-export commonly used types for convenience
 */

export type {
  ErrorResponse,
  PaginatedResponse,
  PaginationParams,
  FilterParams,
  ListParams,
  CreateRequest,
  UpdateRequest,
  AuthResponse,
  LoginRequest,
  FieldErrors,
  ApiError,
} from '@/types/api'

export type {
  BaseEntity,
  Tenant,
  User,
  Person,
  Client,
  ClientContactInfo,
  ClientBillingAddress,
  ClientStats,
  Contract,
  Service,
  ServiceSession,
  ServiceAssignment,
  Document,
  KPI,
  KPIAssignment,
  Contact,
  Activity,
  Industry,
  ClientTag,
  AuditLog,
  Address,
  ContactInfo,
} from '@/types/entities'

export * from '@/types/enums'
