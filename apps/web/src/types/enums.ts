/**
 * Status Enums
 * All status values used across the application
 */

/**
 * Base status used by most entities
 */
export enum BaseStatus {
  ACTIVE = 'Active',
  INACTIVE = 'Inactive',
  PENDING = 'Pending',
  ARCHIVED = 'Archived',
  DELETED = 'Deleted',
}

/**
 * User account status
 */
export enum UserStatus {
  ACTIVE = 'Active',
  SUSPENDED = 'Suspended',
  BANNED = 'Banned',
  TERMINATED = 'Terminated',
  PENDING_VERIFICATION = 'Pending Verification',
  INACTIVE = 'Inactive',
}

/**
 * Tenant/organization status
 */
export enum TenantStatus {
  ACTIVE = 'Active',
  SUSPENDED = 'Suspended',
  TERMINATED = 'Terminated',
  ARCHIVED = 'Archived',
}

/**
 * Contract status
 */
export enum ContractStatus {
  ACTIVE = 'Active',
  EXPIRED = 'Expired',
  TERMINATED = 'Terminated',
  RENEWED = 'Renewed',
  PENDING = 'Pending',
  DRAFT = 'Draft',
}

/**
 * Service session status
 */
export enum SessionStatus {
  SCHEDULED = 'Scheduled',
  RESCHEDULED = 'Rescheduled',
  COMPLETED = 'Completed',
  CANCELLED = 'Cancelled',
  NO_SHOW = 'No Show',
}

/**
 * Document status
 */
export enum DocumentStatus {
  DRAFT = 'Draft',
  PUBLISHED = 'Published',
  ARCHIVED = 'Archived',
  EXPIRED = 'Expired',
}

/**
 * Person types
 */
export enum PersonType {
  PLATFORM_STAFF = 'PlatformStaff',
  CLIENT_EMPLOYEE = 'ClientEmployee',
  DEPENDENT = 'Dependent',
  SERVICE_PROVIDER = 'ServiceProvider',
}

/**
 * Work status
 */
export enum WorkStatus {
  ACTIVE = 'Active',
  INACTIVE = 'Inactive',
  ON_LEAVE = 'On Leave',
  TERMINATED = 'Terminated',
  SUSPENDED = 'Suspended',
  RESIGNED = 'Resigned',
}

/**
 * Staff role (platform staff)
 */
export enum StaffRole {
  ADMIN = 'Admin',
  MANAGER = 'Manager',
  COORDINATOR = 'Coordinator',
  SUPPORT = 'Support',
  VIEWER = 'Viewer',
}

/**
 * Contact methods
 */
export enum ContactMethod {
  EMAIL = 'email',
  PHONE = 'phone',
  SMS = 'sms',
  WHATSAPP = 'whatsapp',
  WECHAT = 'wechat',
}

/**
 * Language codes (ISO 639-1)
 */
export enum Language {
  EN = 'en',
  ES = 'es',
  FR = 'fr',
  DE = 'de',
  IT = 'it',
  PT = 'pt',
  ZH = 'zh',
  JA = 'ja',
  KO = 'ko',
}

/**
 * Payment status
 */
export enum PaymentStatus {
  PENDING = 'Pending',
  PAID = 'Paid',
  OVERDUE = 'Overdue',
  CANCELLED = 'Cancelled',
  REFUNDED = 'Refunded',
}

/**
 * Payment frequency
 */
export enum PaymentFrequency {
  WEEKLY = 'Weekly',
  MONTHLY = 'Monthly',
  QUARTERLY = 'Quarterly',
  ANNUALLY = 'Annually',
}

/**
 * Document types
 */
export enum DocumentType {
  CONTRACT = 'Contract',
  CERTIFICATION = 'Certification',
  KPI_REPORT = 'KPI Report',
  FEEDBACK_SUMMARY = 'Feedback Summary',
  BILLING_REPORT = 'Billing Report',
  UTILIZATION_REPORT = 'Utilization Report',
  OTHER = 'Other',
}

/**
 * KPI categories
 */
export enum KPICategory {
  UTILIZATION = 'Utilization',
  SATISFACTION = 'Satisfaction',
  OUTCOME = 'Outcome',
  OPERATIONAL = 'Operational',
}

/**
 * KPI measurement units
 */
export enum MeasurementUnit {
  PERCENTAGE = 'Percentage',
  COUNT = 'Count',
  RATE = 'Rate',
  SCORE = 'Score',
  TIME = 'Time',
  CURRENCY = 'Currency',
}

/**
 * Activity types
 */
export enum ActivityType {
  CALL = 'CALL',
  EMAIL = 'EMAIL',
  MEETING = 'MEETING',
  NOTE = 'NOTE',
}

/**
 * Relationship types for dependents
 */
export type RelationType =
  | 'Child'
  | 'Spouse'
  | 'Parent'
  | 'Sibling'
  | 'Grandparent'
  | 'Guardian'
  | 'Other'

/**
 * Client tier — assigned by ops, drives reporting and SLA expectations.
 * Tier A = anchor/strategic, Tier B = standard, Tier C = transactional.
 */
export enum ClientTier {
  A = 'A',
  B = 'B',
  C = 'C',
}

/**
 * Critical incident severity (CISM v1).
 */
export enum IncidentSeverity {
  LOW = 'Low',
  MEDIUM = 'Medium',
  HIGH = 'High',
  CRITICAL = 'Critical',
}

/**
 * Lifecycle status of a critical incident record.
 */
export enum IncidentStatus {
  OPEN = 'Open',
  IN_PROGRESS = 'In Progress',
  RESOLVED = 'Resolved',
  CLOSED = 'Closed',
}

/**
 * Contract pricing models (D-Pricing v1).
 * - RETAINER: monthly fixed fee, optional cap on sessions.
 * - FRAMEWORK: deposit drawn down per session at unit rate.
 * - FFS: pay-per-session at unit rate, no commitment.
 * - ADMIN_UTILISATION: monthly admin fee + per-session rate; admin floor enforced.
 * - VALUE_ADD: bundled fee covering services + outcomes (e.g. CISM, reports).
 */
export enum PricingModel {
  RETAINER = 'Retainer',
  FRAMEWORK = 'Framework',
  FFS = 'FFS',
  ADMIN_UTILISATION = 'Admin+Utilisation',
  VALUE_ADD = 'Value-Add',
}

export enum ProviderTier {
  T1 = 'T1',
  T2 = 'T2',
  T3 = 'T3',
}

export enum ProviderRegion {
  NAIROBI = 'Nairobi',
  COAST = 'Coast',
  RIFT = 'Rift',
  WESTERN = 'Western',
  CENTRAL = 'Central',
  REMOTE = 'Remote / Telehealth',
}

export enum AccreditationStatus {
  ACTIVE = 'Active',
  PENDING_RENEWAL = 'Pending Renewal',
  EXPIRED = 'Expired',
  SUSPENDED = 'Suspended',
}

export enum IncidentTimelineEventKind {
  CREATED = 'Created',
  TRIAGE = 'Triage',
  COMMS = 'Comms',
  SESSION_LINKED = 'Session Linked',
  AFTER_ACTION = 'After Action',
  RESOLVED = 'Resolved',
  NOTE = 'Note',
}

/**
 * Action types for audit logs
 */
export enum ActionType {
  CREATE = 'CREATE',
  UPDATE = 'UPDATE',
  DELETE = 'DELETE',
  LOGIN = 'LOGIN',
  LOGOUT = 'LOGOUT',
  APPROVE = 'APPROVE',
  REJECT = 'REJECT',
  LIST = 'LIST',
  VIEW = 'VIEW',
  EXPORT = 'EXPORT',
  IMPORT = 'IMPORT',
}
