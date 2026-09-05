import { screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"

import { ClientContactsPanel } from "@/components/clients/ClientManagementPanels"
import { renderWithProviders } from "@/test/utils"
import type { Client, Contact } from "@/types/entities"

vi.mock("@/api/endpoints/contacts", () => ({
  contactsApi: {
    byClient: vi.fn().mockResolvedValue([]),
    create: vi.fn(),
    setPrimary: vi.fn(),
    remove: vi.fn(),
  },
}))

function client(over: Partial<Client> = {}): Client {
  return { id: "client-1", name: "Minet Uganda", ...over } as Client
}

function contact(over: Partial<Contact> = {}): Contact {
  return {
    id: "c1",
    client_id: "client-1",
    name: "Doreen Muwulya",
    is_primary: false,
    ...over,
  } as Contact
}

/**
 * The panel picks its primary contact out of the list it is given, so an empty
 * list is the boundary worth pinning: a client with no contacts yet. It has to
 * render, because throwing here takes the whole detail page down through the
 * error boundary rather than degrading to an empty state.
 *
 * These assert only that it renders. The panel's copy is still being shaped,
 * and pinning wording would break on edits that are not defects.
 */
describe("ClientContactsPanel", () => {
  const cases: Array<[string, Client, Contact[]]> = [
    ["no contacts and no client details", client(), []],
    ["no contacts but client details", client({ contact_info: { email: "a@b.test" } }), []],
    ["a contact that is not primary", client(), [contact()]],
    ["a contact that is primary", client(), [contact({ is_primary: true })]],
  ]

  it.each(cases)("renders with %s", (_label, c, contacts) => {
    expect(() =>
      renderWithProviders(
        <ClientContactsPanel clientId="client-1" client={c} contacts={contacts} />,
      ),
    ).not.toThrow()
  })

  it("shows contact details entered during client creation", () => {
    renderWithProviders(
      <ClientContactsPanel
        clientId="client-1"
        client={client({ contact_info: { email: "hello@example.com", phone: "+256700000000" } })}
        contacts={[]}
      />,
    )

    expect(screen.getByText("Main contact")).toBeInTheDocument()
    expect(screen.queryByText("Client contact")).not.toBeInTheDocument()
    expect(screen.getByText("hello@example.com · +256700000000")).toBeInTheDocument()
  })
})
