import { describe, expect, it } from "vitest"

import { boolParam, enumOrArrayParam, enumParam, listSearchSchema } from "@/lib/search-params"

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
  it('accepts the numeric form the router decodes a written "1" into', () => {
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

describe("enumOrArrayParam", () => {
  const parse = enumOrArrayParam(Tier)

  it("accepts a single valid value, unwrapped", () => {
    expect(parse("A")).toBe("A")
  })

  it("accepts several values as an array", () => {
    expect(parse(["A", "B"])).toEqual(["A", "B"])
  })

  it("collapses a one-element array back to a single value", () => {
    expect(parse(["A"])).toBe("A")
  })

  it("drops invalid members and keeps the valid ones", () => {
    expect(parse(["A", "Z"])).toBe("A")
  })

  it("is undefined for an unknown value or an all-invalid array", () => {
    expect(parse("Z")).toBeUndefined()
    expect(parse(["Z"])).toBeUndefined()
    expect(parse([])).toBeUndefined()
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

  it("carries the table state the list hooks keep in the URL", () => {
    expect(validate({ page: 3, sort: "name", desc: true })).toEqual({
      page: 3,
      sort: "name",
      desc: true,
    })
  })

  it("accepts the string forms a hand-typed URL produces", () => {
    expect(validate({ page: "4", desc: "true", sort: "status" })).toEqual({
      page: 4,
      sort: "status",
      desc: true,
    })
  })

  /** Page 1 and ascending are the defaults, so they leave no trace in the URL. */
  it("drops page 1, a fractional or negative page, and an unset desc", () => {
    expect(validate({ page: 1, desc: false })).toEqual({})
    expect(validate({ page: 0 })).toEqual({})
    expect(validate({ page: -2 })).toEqual({})
    expect(validate({ page: 2.5 })).toEqual({})
    expect(validate({ page: "many" })).toEqual({})
  })
})
