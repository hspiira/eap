import { Link, useRouterState } from "@tanstack/react-router"

import { cn } from "@/lib/utils"

const SECTIONS = [
  { to: "/providers", label: "Practitioners" },
  { to: "/provider-organisations", label: "Organisations" },
  { to: "/provider-aliases", label: "Name aliases" },
] as const

/** Switches between the sections of the Providers module. */
export function ProviderSectionTabs() {
  const pathname = useRouterState({ select: (s) => s.location.pathname })
  return (
    <div role="tablist" className="flex h-10 shrink-0 items-end gap-0.5 border-b border-fg/10 px-3">
      {SECTIONS.map((section) => {
        const active = pathname === section.to || pathname.startsWith(`${section.to}/`)
        return (
          <Link
            key={section.to}
            to={section.to}
            role="tab"
            aria-selected={active}
            className={cn(
              "relative -mb-px flex h-9 shrink-0 items-center rounded-none border-b-2 border-transparent px-2.5 text-sm font-medium text-fg/60 hover:text-fg",
              active && "border-primary text-fg",
            )}
          >
            {section.label}
          </Link>
        )
      })}
    </div>
  )
}
