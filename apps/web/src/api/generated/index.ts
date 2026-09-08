/**
 * Named re-exports of the backend types in `./schema.ts`.
 *
 * `schema.ts` is generated from `apps/api/schema/openapi.json` and must not be
 * edited by hand; run `pnpm contracts:sync` to regenerate it. This barrel is
 * maintained by hand, so add an export here when a form needs a new type.
 *
 * Usage:
 *   import type { ClientCreate, ContractCreate } from "@/api/generated"
 *
 * The convention here is: a Zod schema's parsed output should `satisfies` the
 * matching `*Create` / `*Update` type from this module. That makes BE↔FE
 * contract drift a TypeScript compile error.
 *
 *   import { z } from "zod"
 *   import type { ClientCreate } from "@/api/generated"
 *   const clientCreateSchema = z.object({ ... })
 *   type _Check = z.infer<typeof clientCreateSchema> extends ClientCreate ? true : never
 */

import type { components } from "./schema"

export type Schemas = components["schemas"]

// ----- Clients ---------------------------------------------------------------
export type ClientCreate = Schemas["ClientCreate"]
export type ClientUpdate = Schemas["ClientUpdate"]
export type ClientResponse = Schemas["ClientResponse"]
export type ClientStatsResponse = Schemas["ClientStatsResponse"]
export type AddressCreate = Schemas["AddressCreate"]
export type ContactInfoCreate = Schemas["ContactInfoCreate"]
export type ContactMethod = Schemas["ContactMethod"]
export type ClientTier = Schemas["ClientTier"]

// ----- Legacy person form types ---------------------------------------------
// The Persons API is retired. These local shapes keep the dormant compatibility
// form compiling without reintroducing retired OpenAPI operations.
export type PersonCreate = Record<string, unknown>
export type EmploymentInfoCreateSchema = Record<string, unknown>
export type DependentInfoSchema = Record<string, unknown>
export type PersonType = string

// ----- Contracts -------------------------------------------------------------
export type ContractCreate = Schemas["ContractCreate"]
export type ContractUpdate = Schemas["ContractUpdate"]
export type ContractRenewRequest = Schemas["ContractRenewRequest"]
export type ContractTerminateRequest = Schemas["ContractTerminateRequest"]
/** Money used inside ContractCreate.billing_rate (BE has a duplicate-named class in this module). */
export type MoneySchema = Schemas["app__api__schemas__contract_schemas__MoneySchema"]
/** Money used in ContractRenewRequest.new_rate / ContractUpdate.billing_rate. */
export type MoneyCreate = Schemas["MoneyCreate"]
export type PaymentFrequency = Schemas["PaymentFrequency"]

// ----- Services --------------------------------------------------------------
export type ServiceCreate = Schemas["ServiceCreate"]
export type ServiceUpdate = Schemas["ServiceUpdate"]
export type ServiceUpdateGroupSettings = Schemas["ServiceUpdateGroupSettings"]

// ----- Service sessions ------------------------------------------------------
export type ServiceSessionCreate = Schemas["ServiceSessionCreate"]
export type ServiceSessionCompleteRequest = Schemas["ServiceSessionCompleteRequest"]

// ----- Service assignments ---------------------------------------------------
export type ServiceAssignmentCreate = Schemas["ServiceAssignmentCreate"]
export type ServiceAssignmentUpdate = Schemas["ServiceAssignmentUpdate"]

// ----- Users -----------------------------------------------------------------
export type UserCreate = Schemas["UserCreate"]

// ----- Surveys ---------------------------------------------------------------
export type SurveyCampaignCreate = Schemas["SurveyCampaignCreate"]

// ----- Engagements -----------------------------------------------------------
export type EngagementCreate = Schemas["EngagementCreate"]
export type DeliverableCreate = Schemas["DeliverableCreate"]
export type HoursLogCreate = Schemas["HoursLogCreate"]

// ----- Care callbacks --------------------------------------------------------
export type CareCallbackCampaignCreate = Schemas["CareCallbackCampaignCreate"]

// ----- Dashboard -------------------------------------------------------------
export type DashboardResponse = Schemas["DashboardResponse"]
export type DashboardKpis = Schemas["DashboardKpis"]
export type RangeInfo = Schemas["RangeInfo"]
export type SeriesPoint = Schemas["SeriesPoint"]
export type ServiceTrend = Schemas["ServiceTrend"]
export type CategoryCount = Schemas["CategoryCount"]
export type ClientSessions = Schemas["ClientSessions"]
export type ImportQueueEntry = Schemas["ImportQueueEntry"]
export type ImportBatchSummary = Schemas["ImportBatchSummary"]
export type DataQuality = Schemas["DataQuality"]

// ----- Global search ---------------------------------------------------------
export type GlobalSearchRequest = Schemas["GlobalSearchRequest"]
export type GlobalSearchResponse = Schemas["GlobalSearchResponse"]
export type SearchCategoryResult = Schemas["SearchCategoryResult"]
export type SearchResultItem = Schemas["SearchResultItem"]
