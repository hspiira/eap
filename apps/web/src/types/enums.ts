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

/** Physical or online delivery. */
export enum SessionType {
  PHYSICAL = 'Physical',
  ONLINE = 'Online',
}

/** Session composition. Group requires a headcount of at least 2. */
export enum SessionCategory {
  INDIVIDUAL = 'Individual',
  GROUP = 'Group',
  FAMILY = 'Family',
  COUPLES = 'Couples',
}

/** Whether the person is new to the service or returning. */
export enum ClientType {
  NEW = 'New',
  REPEAT = 'Repeat',
}

/**
 * Clinical continuation outcome recorded at session end.
 * Distinct from SessionStatus (the scheduling lifecycle).
 */
export enum SessionClinicalStatus {
  TO_BE_CONTINUED = 'ToBeContinued',
  REFERRED = 'Referred',
  COMPLETED = 'Completed',
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

/** Lifecycle of an EAP-eligible member as supplied by the employer. */
export enum EligibilityStatus {
  ACTIVE = 'Active',
  SUSPENDED = 'Suspended',
  TERMINATED = 'Terminated',
  PENDING = 'Pending',
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
 * Relationship of an EligibleMember to the primary employee. Distinct from
 * RelationType (used for DependentInfo) — similar-looking but a different
 * enum on the wire; do not conflate the two.
 */
export enum MemberRelation {
  EMPLOYEE = 'Employee',
  SPOUSE = 'Spouse',
  CHILD = 'Child',
  DOMESTIC_PARTNER = 'DomesticPartner',
  DEPENDENT_OTHER = 'DependentOther',
}

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
  KAMPALA = 'Kampala',
  CENTRAL = 'Central',
  EASTERN = 'Eastern',
  WESTERN = 'Western',
  NORTHERN = 'Northern',
  REMOTE = 'Remote / Telehealth',
}

/**
 * Provider accreditation lifecycle — mirrors BE `AccreditationStatus`.
 */
export enum AccreditationStatus {
  PENDING = 'Pending',
  ACCREDITED = 'Accredited',
  LAPSED = 'Lapsed',
  SUSPENDED = 'Suspended',
  REJECTED = 'Rejected',
}

/**
 * Whether a provider is currently on the active panel — mirrors BE `PanelStatus`.
 */
export enum PanelStatus {
  ACTIVE = 'Active',
  SUSPENDED = 'Suspended',
  REMOVED = 'Removed',
}

/**
 * Lifecycle of a non-compete clause — mirrors BE `NonCompeteStatus`.
 */
export enum NonCompeteStatus {
  DRAFT = 'Draft',
  ACTIVE = 'Active',
  REVOKED = 'Revoked',
  EXPIRED = 'Expired',
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
 * Lifecycle status of a counsellor-initiated care-callback campaign.
 * Wire-true: Draft -> Active -> Completed, with Draft -> Archived also
 * allowed (skip straight to archived without ever activating).
 */
export enum CareCallbackCampaignStatus {
  DRAFT = 'Draft',
  ACTIVE = 'Active',
  COMPLETED = 'Completed',
  ARCHIVED = 'Archived',
}

/**
 * Status of a single outreach record within a campaign.
 * Pending -> Assigned -> Contacted -> one of the four terminal statuses.
 */
export enum OutreachStatus {
  PENDING = 'Pending',
  ASSIGNED = 'Assigned',
  CONTACTED = 'Contacted',
  COMPLETED = 'Completed',
  UNREACHABLE = 'Unreachable',
  DECLINED = 'Declined',
  ESCALATED = 'Escalated',
}

/** Auto-derived risk classification from a scored triage instrument. */
export enum TriageRiskLevel {
  LOW = 'Low',
  MODERATE = 'Moderate',
  HIGH = 'High',
  CRITICAL = 'Critical',
}

/** The 12 standardised triage instruments the BE's catalogue can score. */
export enum TriageInstrumentCode {
  JOSEPH7 = 'JOSEPH7',
  WOS5 = 'WOS5',
  PHQ9 = 'PHQ9',
  GAD7 = 'GAD7',
  CSSRS = 'CSSRS',
  AUDIT_C = 'AUDIT_C',
  DAST10 = 'DAST10',
  WHO5 = 'WHO5',
  K10 = 'K10',
  WSAS = 'WSAS',
  DASS21 = 'DASS21',
  PCL5 = 'PCL5',
}

/** Stage-of-change, derived by some instruments (e.g. JOSEPH7). */
export enum StageOfChange {
  PRECONTEMPLATION = 'Precontemplation',
  CONTEMPLATION = 'Contemplation',
  PREPARATION = 'Preparation',
  ACTION = 'Action',
  MAINTENANCE = 'Maintenance',
}

/**
 * Question types used by the dynamic Questionnaire renderer (Phase 3 #1 triage form).
 * Mirrors the BE shape; renderer dispatches on this discriminator.
 */
export enum QuestionnaireQuestionType {
  SCALE = 'Scale',
  SINGLE_CHOICE = 'SingleChoice',
  MULTI_CHOICE = 'MultiChoice',
  TEXT = 'Text',
  YES_NO = 'YesNo',
}

/**
 * When the questionnaire is administered relative to the session.
 * Joseph 7-variable + WOS-5 are run pre + post; outcome reports diff the two.
 */
export enum QuestionnaireAdministration {
  PRE = 'Pre',
  POST = 'Post',
  STANDALONE = 'Standalone',
}

/**
 * Lifecycle status of a Survey campaign (Phase 3 #2).
 * - DRAFT: webhook not yet wired; no responses accepted.
 * - COLLECTING: webhook live; responses streaming in.
 * - CLOSED: response window closed; aggregates finalised.
 */
export enum SurveyStatus {
  DRAFT = 'Draft',
  COLLECTING = 'Collecting',
  CLOSED = 'Closed',
}

/**
 * Source platform for Survey responses. Phase 3 v1 ships Google Forms; the BE keeps
 * the union open so we can add SurveyMonkey / Typeform without a schema change.
 */
export enum SurveySource {
  MICROSOFT_FORMS = 'Microsoft Forms',
  GOOGLE_FORMS = 'Google Forms',
  TYPEFORM = 'Typeform',
  SURVEY_MONKEY = 'SurveyMonkey',
  CUSTOM = 'Custom',
}

/**
 * Consultancy engagement lifecycle (Phase 4 #1). Linear FSM:
 * SCOPING → ACTIVE → DELIVERED → CLOSED. CANCELLED is a terminal off-ramp from any state.
 */
export enum EngagementStatus {
  SCOPING = 'Scoping',
  ACTIVE = 'Active',
  DELIVERED = 'Delivered',
  CLOSED = 'Closed',
  CANCELLED = 'Cancelled',
}

/**
 * Type of consultancy engagement. Drives default rate-card lookup BE-side and the
 * "kind" badge in the FE.
 */
export enum EngagementType {
  POLICY_DRAFT = 'Policy Draft',
  TRAINING = 'Training',
  ASSESSMENT = 'Assessment',
  ADVISORY = 'Advisory',
  AUDIT = 'Audit',
  OTHER = 'Other',
}

/**
 * Engagement deliverable status — independent from the parent engagement's status.
 */
export enum DeliverableStatus {
  PENDING = 'Pending',
  IN_PROGRESS = 'In Progress',
  SUBMITTED = 'Submitted',
  ACCEPTED = 'Accepted',
  REJECTED = 'Rejected',
}

/**
 * Engagement timeline event kinds. Mirrors the IncidentTimeline pattern.
 */
export enum EngagementTimelineEventKind {
  CREATED = 'Created',
  STATUS_CHANGED = 'Status Changed',
  DELIVERABLE_ADDED = 'Deliverable Added',
  DELIVERABLE_UPDATED = 'Deliverable Updated',
  HOURS_LOGGED = 'Hours Logged',
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

/**
 * Authentication credential type per user.
 */
export enum AuthProvider {
  PASSWORD = 'password',
  AZURE_AD = 'azure_ad',
}

/**
 * Role of a user within their tenant (RBAC).
 */
export enum TenantRole {
  ADMIN = 'Admin',
  USER = 'User',
  VIEWER = 'Viewer',
}

/**
 * Per-user grants gating the clinical / employer bounded contexts.
 * Clinical guards PHI surfaces; only platform admins may grant it.
 */
export enum AccessScope {
  CLINICAL = 'Clinical',
  EMPLOYER_PORTAL = 'EmployerPortal',
}

/** Lifecycle of a clinical case. */
export enum CaseStatus {
  INTAKE = 'Intake',
  ASSESSMENT = 'Assessment',
  ACTIVE = 'Active',
  CLOSED = 'Closed',
  REFERRED_OUT = 'ReferredOut',
  NO_SHOW_CLOSED = 'NoShowClosed',
}

export enum CaseReferralSource {
  SELF = 'Self',
  INFORMAL_MANAGER = 'InformalManager',
  FORMAL_MANDATORY = 'FormalMandatory',
  HR = 'HR',
  CISM_FOLLOW_UP = 'CISMFollowUp',
  EMPLOYER_PROACTIVE = 'EmployerProactive',
}

export enum PresentingProblem {
  MENTAL_HEALTH = 'MentalHealth',
  STRESS = 'Stress',
  RELATIONSHIP = 'Relationship',
  WORK = 'Work',
  FINANCIAL = 'Financial',
  SUBSTANCE = 'Substance',
  BEREAVEMENT = 'Bereavement',
  TRAUMA = 'Trauma',
  FAMILY_CHILD = 'FamilyChild',
  OTHER = 'Other',
}

export enum CaseClosureReason {
  GOALS_MET = 'GoalsMet',
  CLIENT_DISCONTINUED = 'ClientDiscontinued',
  REFERRED_OUT = 'ReferredOut',
  NO_SHOW = 'NoShow',
  SESSION_CAP_REACHED = 'SessionCapReached',
  INELIGIBLE = 'Ineligible',
  OTHER = 'Other',
}

/** Note template — each shapes a different `body` on the wire (see clinical-notes API). */
export enum ClinicalNoteType {
  DAP = 'DAP',
  SOAP = 'SOAP',
  PHONE_CONTACT = 'PhoneContact',
  CRISIS_CONTACT = 'CrisisContact',
  CLOSURE_SUMMARY = 'ClosureSummary',
  SUPERVISION = 'Supervision',
}

/** Session-cap authorization lifecycle. */
export enum AuthorizationStatus {
  ACTIVE = 'Active',
  EXTENSION_REQUESTED = 'ExtensionRequested',
  EXTENDED = 'Extended',
  EXHAUSTED = 'Exhausted',
  EXPIRED = 'Expired',
  CLOSED = 'Closed',
}

/** Billable service category an authorization's session cap applies to. */
export enum ServiceCategory {
  SHORT_TERM_COUNSELLING = 'ShortTermCounselling',
  CRISIS_INTERVENTION = 'CrisisIntervention',
  SUBSTANCE_USE = 'SubstanceUse',
  MANAGER_CONSULT = 'ManagerConsult',
  WORK_LIFE_REFERRAL = 'WorkLifeReferral',
  CISM_RESPONSE = 'CISMResponse',
  WELLNESS_COACHING = 'WellnessCoaching',
}
