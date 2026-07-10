/**
 * BE-canonical types, generated from `evexia_bk/schema/openapi.json`.
 *
 * Do not edit by hand. Regenerate with `pnpm openapi:sync`.
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
export type AddressCreate = Schemas["AddressCreate"]
export type ContactInfoCreate = Schemas["ContactInfoCreate"]
export type ContactMethod = Schemas["ContactMethod"]
export type ClientTier = Schemas["ClientTier"]

// ----- Persons ---------------------------------------------------------------
export type PersonCreate = Schemas["PersonCreate"]
export type EmploymentInfoCreateSchema = Schemas["EmploymentInfoCreateSchema"]
export type DependentInfoSchema = Schemas["DependentInfoSchema"]
export type PersonType = Schemas["PersonType"]

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
