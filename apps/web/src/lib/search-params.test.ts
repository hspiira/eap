import { describe, expect, it } from "vitest"

import { boolParam, enumParam, listSearchSchema } from "@/lib/search-params"

enum Tier {
  A = "A",
  B = "B",
}

describe("boolParam", () => {
  const parse = boolParam()

  it("accepts what the router decodes a written flag into", () => {
    expect(parse(true)).toBe(true)
  })

  it("accepts the hand-typed URL form", () => {
    expect(parse("true")).toBe(true)
  })

  /**
   * `setFilter` writes the string "1", which the router serialises to `?flag=1`
   * and decodes back as the number 1. Checking only for the string left the
   * filter off after a reload. Both forms are covered so that cannot return.
   */
  it("accepts the numeric form the router decodes a written \"1\" into", () => {
    expect(parse(1)).toBe(true)
    expect(parse("1")).toBe(true)
  })

  it("treats anything else as absent, so the default leaves no query string", () => {
    expect(parse("0")).toBeUndefined()
    expect(parse(false)).toBeUndefined()
    expect(parse(undefined)).toBeUndefined()
    expect(parse("")).toBeUndefined()
  })
})

describe("listSearchSchema with a flag", () => {
  const validate = listSearchSchema({ tier: enumParam(Tier), archived: boolParam() })

  it("keeps a set flag alongside other filters", () => {
    expect(validate({ tier: "A", archived: true })).toEqual({ tier: "A", archived: true })
  })

  it("omits the flag entirely when it is not set", () => {
    expect(validate({ tier: "A" })).toEqual({ tier: "A" })
    expect(validate({ tier: "A", archived: 0 })).toEqual({ tier: "A" })
  })

  it("rejects a tier that is not in the enum", () => {
    expect(validate({ tier: "Z" })).toEqual({})
  })

  it("still handles the shared new and search params", () => {
    expect(validate({ new: "1", search: "acme" })).toEqual({ new: true, search: "acme" })
    expect(validate({ search: "   " })).toEqual({})
  })
})
