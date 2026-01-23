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
