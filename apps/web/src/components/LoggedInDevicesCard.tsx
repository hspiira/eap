import { Laptop, Smartphone } from "lucide-react"

import { cn } from "@/lib/utils"

const SESSIONS = [
  {
    device: "2018 MacBook Pro 15-inch",
    location: "Melbourne, Australia",
    time: "22 Jan at 10:42am",
    status: "Active now",
    dotColor: "bg-accent-success",
    badgeClass: "bg-accent-success-soft text-accent-success-ink",
    icon: Laptop,
  },
  {
    device: "2018 MacBook Pro 15-inch",
    location: "Melbourne, Australia",
    time: "22 Jan at 12:15pm",
    status: "Error Login",
    dotColor: "bg-accent-error",
    badgeClass: "bg-accent-error-soft text-accent-error-ink",
    icon: Laptop,
  },
  {
    device: "2022 iPhone XS",
    location: "Melbourne, Australia",
    time: "22 Jan at 15:29pm",
    status: "In Active",
    dotColor: "bg-neutral-400",
    badgeClass: "bg-accent-blue-soft text-accent-blue-ink",
    icon: Smartphone,
  },
]

export function LoggedInDevicesCard() {
  return (
    <div className="flex max-w-[420px] flex-col rounded-xl border border-neutral-200 bg-white shadow-sm">
      <div className="px-4 pt-4 pb-3">
        <h2 className="text-lg font-bold text-neutral-800">Where you're logged in</h2>
        <p className="mt-1.5 text-sm leading-snug text-neutral-500">
          We'll alert you via{" "}
          <span className="font-semibold font-mono text-neutral-500">admin@untitled.com</span>{" "}
          if there is any unusual activity on your account.
        </p>
      </div>
      <div className="flex flex-col">
        {SESSIONS.map((s, i) => (
          <div
            key={i}
            className="px-4 py-3"
          >
            <div className="flex gap-3">
              <div className="flex h-8 w-8 shrink-0 items-start justify-center pt-0.5 text-fg-subtle">
                <s.icon className="h-4 w-4" strokeWidth={1.5} />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-neutral-800">{s.device}</p>
                <p className="mt-1 text-xs text-neutral-500">
                  {s.location} • {s.time}
                </p>
                <div className="mt-2">
                  <span
                    className={cn(
                      "inline-flex items-center gap-1.5 rounded-full px-2 py-1 text-xs font-bold",
                      s.badgeClass
                    )}
                  >
                    <span className={cn("h-1.5 w-1.5 shrink-0 rounded-full", s.dotColor)} />
                    {s.status}
                  </span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
