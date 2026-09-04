/**
 * Guards the enums in `types/enums.ts` against the generated API contract.
 *
 * These values go on the wire, and TypeScript cannot check them: an enum member
 * is just a string, so a form can offer "Google Forms" where the API only
 * accepts "GoogleForms" and nothing fails until the request is rejected. Every
 * other request field is now typed from the contract and checked at build time;
 * enum values are the remaining gap, so they are checked here instead.
 */

import { readFileSync } from "node:fs"
import { resolve } from "node:path"

import { describe, expect, it } from "vitest"

import * as appEnums from "./enums"

// vitest runs with apps/web as the working directory.
const SCHEMA_PATH = resolve(process.cwd(), "../api/schema/openapi.json")

interface OpenApiSchema {
  components: { schemas: Record<string, { type?: string; enum?: string[] }> }
}

function contractEnums(): Map<string, string[]> {
  const doc = JSON.parse(readFileSync(SCHEMA_PATH, "utf8")) as OpenApiSchema
  const out = new Map<string, string[]>()
  for (const [name, schema] of Object.entries(doc.components.schemas)) {
    if (schema.type === "string" && Array.isArray(schema.enum)) out.set(name, schema.enum)
  }
  return out
}

/** The string enums exported from `types/enums.ts`, by name. */
function frontendEnums(): Map<string, string[]> {
  const out = new Map<string, string[]>()
  for (const [name, value] of Object.entries(appEnums)) {
    if (typeof value !== "object" || value === null) continue
    const members = Object.values(value)
    if (members.length > 0 && members.every((m) => typeof m === "string")) {
      out.set(name, members as string[])
    }
  }
  return out
}

describe("enum values match the API contract", () => {
  const api = contractEnums()
  const fe = frontendEnums()
  const shared = [...fe.keys()].filter((name) => api.has(name)).sort()

  it("finds enums on both sides to compare", () => {
    expect(api.size).toBeGreaterThan(0)
    expect(shared.length).toBeGreaterThan(20)
  })

  it.each(shared)("%s offers only values the API accepts", (name) => {
    const accepted = new Set(api.get(name))
    const rejected = fe.get(name)!.filter((v) => !accepted.has(v))
    expect(rejected, `${name} offers values the API rejects`).toEqual([])
  })

  it.each(shared)("%s offers every value the API can return", (name) => {
    const offered = new Set(fe.get(name))
    const missing = api.get(name)!.filter((v) => !offered.has(v))
    expect(missing, `${name} is missing values the API can return`).toEqual([])
  })
})
