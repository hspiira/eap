/**
 * Survey campaign API (Phase 3 #3).
 *
 * BE base path is `/survey-campaigns`. The list envelope, filters, sort and
 * paging are the API's; the fixture applies the same ones to its own store so
 * both modes answer the same contract (MODULES_REPAIR_PLAN API-01).
 *
 * The webhook secret is supplied on create and never returned afterwards, so
 * no adapter here reads one back.
 */

import { useFixtures } from "@/lib/fixtures"
import type { SurveyStatusValue } from "@/types/entities"

import apiClient from "../client"
import type { ListParams, Survey, SurveyAggregate, SurveyList } from "../types"
import {
  fixtureActivateSurvey,
  fixtureCloseSurvey,
  fixtureCreateSurvey,
  fixtureGetSurvey,
  fixtureListSurveys,
  fixtureSurveyAggregate,
  type SurveyCreateInput,
} from "./surveys-fixture"

/** Mirrors the query params on `GET /survey-campaigns` in the BE OpenAPI schema. */
export interface SurveyListParams extends ListParams {
  status?: SurveyStatusValue
  client_id?: string
}

export const surveysApi = {
  async list(params?: SurveyListParams): Promise<SurveyList> {
    if (useFixtures()) return Promise.resolve(fixtureListSurveys(params))
    return apiClient.get<SurveyList>("/survey-campaigns", params)
  },

  async getById(id: string): Promise<Survey> {
    if (useFixtures()) {
      const found = fixtureGetSurvey(id)
      if (!found) throw new Error(`Survey ${id} not found`)
      return Promise.resolve(found)
    }
    return apiClient.get<Survey>(`/survey-campaigns/${id}`)
  },

  async create(input: SurveyCreateInput): Promise<Survey> {
    if (useFixtures()) return Promise.resolve(fixtureCreateSurvey(input))
    return apiClient.post<Survey>("/survey-campaigns", input)
  },

  async activate(id: string): Promise<Survey> {
    if (useFixtures()) return Promise.resolve(fixtureActivateSurvey(id))
    return apiClient.post<Survey>(`/survey-campaigns/${id}/activate`, {})
  },

  async close(id: string): Promise<Survey> {
    if (useFixtures()) return Promise.resolve(fixtureCloseSurvey(id))
    return apiClient.post<Survey>(`/survey-campaigns/${id}/close`, {})
  },

  async getAggregate(id: string): Promise<SurveyAggregate> {
    if (useFixtures()) return Promise.resolve(fixtureSurveyAggregate(id))
    return apiClient.get<SurveyAggregate>(`/survey-campaigns/${id}/aggregate`)
  },
}

export type { SurveyCreateInput } from "./surveys-fixture"
