/**
 * Practitioner name reconciliation.
 *
 * An alias is one source system's spelling of a practitioner's name and the
 * decision a person made about it. Historical session import reads those
 * decisions and never opens one: a row whose name has no resolved alias is
 * held, not guessed, so importing a name for the first time means queueing it
 * here and then naming the practitioner.
 *
 * There is no automatic resolve. The API requires a person to choose, and
 * records who chose, because a wrong mapping silently reattributes past work.
 * Every write below is Admin-only and audited.
 */

import type { components } from "@/api/generated/schema"
import type { AliasResolutionState } from "@/types/enums"

import apiClient from "../client"
import type { ListParams, PaginatedResponse } from "../types"

export type ProviderAlias = components["schemas"]["ProviderAliasResponse"]

export interface ProviderAliasListParams extends ListParams {
  /** Required: the alias routes scope by query parameter, not by header. */
  tenant_id: string
  source_system?: string
  state?: AliasResolutionState
  /** Only the spellings resolved to this practitioner. */
  provider_id?: string
}

/** Tenant travels in the query string on every alias route, writes included. */
function scoped(path: string, tenantId: string): string {
  return `${path}?${new URLSearchParams({ tenant_id: tenantId })}`
}

export const providerAliasesApi = {
  async list(params: ProviderAliasListParams): Promise<PaginatedResponse<ProviderAlias>> {
    return apiClient.get<PaginatedResponse<ProviderAlias>>("/provider-aliases", params)
  },

  /**
   * Put a source name into the review queue, unmapped.
   *
   * Queueing attributes nothing. Asking twice returns the entry already there,
   * so this cannot split one name across two entries or reopen a decision.
   */
  async create(
    tenantId: string,
    data: { source_system: string; source_value: string },
  ): Promise<ProviderAlias> {
    return apiClient.post<ProviderAlias>(scoped("/provider-aliases", tenantId), data)
  },

  /** Record that this source name is this practitioner. */
  async resolve(tenantId: string, aliasId: string, providerId: string): Promise<ProviderAlias> {
    return apiClient.post<ProviderAlias>(scoped(`/provider-aliases/${aliasId}/resolve`, tenantId), {
      provider_id: providerId,
    })
  },

  /**
   * Queue a name and name its practitioner in one step.
   *
   * Refuses to overwrite a decision somebody already made: `create` returns an
   * existing entry rather than a second one, so a name already resolved comes
   * back untouched and the caller is told. Without that guard, creating a
   * practitioner could silently reattribute every session imported under a
   * name that already points at a different person.
   */
  async adopt(
    tenantId: string,
    sourceSystem: string,
    sourceValue: string,
    providerId: string,
  ): Promise<{ alias: ProviderAlias; claimed: boolean }> {
    const existing = await this.create(tenantId, {
      source_system: sourceSystem,
      source_value: sourceValue,
    })
    if (existing.state === "Resolved") return { alias: existing, claimed: false }
    return { alias: await this.resolve(tenantId, existing.id, providerId), claimed: true }
  },

  /** Record that this source value does not name a practitioner. */
  async reject(tenantId: string, aliasId: string, note: string): Promise<ProviderAlias> {
    return apiClient.post<ProviderAlias>(scoped(`/provider-aliases/${aliasId}/reject`, tenantId), {
      note,
    })
  },
}
