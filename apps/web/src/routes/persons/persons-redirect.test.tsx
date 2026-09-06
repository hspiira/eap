import { render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"

vi.mock("@tanstack/react-router", () => ({
  createFileRoute: () => (options: Record<string, unknown>) => ({ options }),
  Navigate: ({ to }: { to: string }) => <span>Redirect to {to}</span>,
}))

const { Route } = await import("@/routes/persons/index")
const Page = (Route as unknown as { options: { component: React.ComponentType } }).options.component

describe("persons compatibility route", () => {
  it("sends the obsolete list to the provider workspace", () => {
    render(<Page />)
    expect(screen.getByText("Redirect to /providers")).toBeInTheDocument()
  })
})
