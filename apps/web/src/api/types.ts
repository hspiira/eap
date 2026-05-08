/**
 * API-specific type definitions
 * Re-export commonly used types for convenience
 */

export type {
  ApiError,
  AuthResponse,
  CreateRequest,
  ErrorResponse,
  FieldErrors,
  FilterParams,
  ListParams,
  LoginRequest,
  PaginatedResponse,
  PaginationParams,
  UpdateRequest,
} from '@/types/api'
export type {
  Activity,
  Address,
  AuditLog,
  BaseEntity,
  Client,
  ClientBillingAddress,
  ClientContactInfo,
  ClientStats,
  ClientTag,
  Contact,
  ContactInfo,
  Contract,
  ContractPricing,
  Diagnosis,
  Document,
  InvoiceLinePreview,
  RateCardItem,
  Incident,
  IncidentTimelineEvent,
  Industry,
  KPI,
  KPIAssignment,
  Person,
  Provider,
  ProviderAccreditation,
  ProviderNonCompete,
  ProviderTierTransition,
  Service,
  ServiceAssignment,
  ServiceSession,
  Tenant,
  User,
} from '@/types/entities'
export * from '@/types/enums'
