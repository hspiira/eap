import { Code, Copy, Download, GripVertical, UserPlus, X } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

const MEMBERS = [
  { name: "Lynel", email: "skrollstudios@gmail.com", role: "Owner" },
  { name: "Karn Frames", email: "karansarao@gmail.com", role: "Can Edit" },
  { name: "Khateeb", email: "khateebreheman@gmail.com", role: "Can View" },
]

export function InviteToProjectCard() {
  return (
    <div className="border border-neutral-200 bg-white rounded-none">
      <div className="flex items-start justify-between p-4 border-b border-dashed border-neutral-200">
        <div className="flex gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border-2 border-dashed border-ink/30 text-ink">
            <UserPlus className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-neutral-800">Invite to Project</h2>
            <p className="mt-0.5 text-xs text-neutral-500">
              Collaborate with members on this project.
            </p>
          </div>
        </div>
        <button
          type="button"
          className="flex h-8 w-8 items-center justify-center text-neutral-500 hover:bg-surface-chip-cool rounded-none"
          aria-label="Close"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
      <div className="space-y-4 p-4">
        <div className="border-b border-neutral-200 pb-4">
          <h3 className="text-xs font-medium text-neutral-800">Link to Share</h3>
          <div className="mt-1 flex flex-wrap items-center justify-between gap-2">
            <p className="text-xs text-neutral-500">Anyone with the link can access</p>
            <select
              className="h-8 border border-neutral-200 bg-neutral-100 pl-2 pr-6 text-xs text-neutral-800 rounded-none appearance-none bg-no-repeat"
              style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%23333333' stroke-width='2'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E")`, backgroundPosition: "right 6px center" }}
              defaultValue="view"
            >
              <option value="view">Can View</option>
              <option value="edit">Can Edit</option>
            </select>
          </div>
          <div className="mt-2 flex gap-2">
            <Input
              className="flex-1 text-sm bg-surface-soft-cool border-neutral-200"
              defaultValue="https://www.figma.com/design/Project-Screen"
              readOnly
            />
            <Button variant="secondary" size="sm" className="shrink-0 gap-1.5 rounded-none">
              <Copy className="h-3.5 w-3.5" />
              Copy
            </Button>
          </div>
        </div>
        <div>
          <h3 className="text-xs font-medium text-neutral-800">Email</h3>
          <div className="mt-2 flex gap-2">
            <div className="relative flex flex-1 items-center">
              <Input
                className="pr-8 rounded-none"
                defaultValue="lynelpatil@gmail.com"
              />
              <button
                type="button"
                className="absolute right-2 flex h-6 w-6 items-center justify-center text-neutral-500 hover:bg-neutral-200 rounded-none"
                aria-label="Remove email"
              >
                <X className="h-3 w-3" />
              </button>
            </div>
            <select
              className="h-9 w-24 shrink-0 border border-neutral-200 bg-neutral-100 px-2 text-xs text-neutral-800 rounded-none appearance-none bg-no-repeat"
              style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%23333333' stroke-width='2'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E")`, backgroundPosition: "right 6px center" }}
              defaultValue="view"
            >
              <option value="view">Can View</option>
              <option value="edit">Can Edit</option>
            </select>
            <Button size="sm" className="shrink-0 bg-neutral-700 text-white hover:bg-neutral-800 rounded-none">
              Send Invite
            </Button>
          </div>
        </div>
        <div>
          <h3 className="text-xs font-medium text-neutral-800">Project Members</h3>
          <ul className="mt-2 divide-y divide-neutral-100">
            {MEMBERS.map((m, i) => (
              <li
                key={m.email}
                className="flex items-center gap-3 py-3 first:pt-0 last:pb-0"
              >
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-surface-chip text-xs font-medium text-neutral-800">
                  {m.name.charAt(0)}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-neutral-800">{m.name}</p>
                  <p className="text-xs text-neutral-500">{m.email}</p>
                </div>
                <select
                  className="h-8 w-28 border border-neutral-200 bg-neutral-100 px-2 text-xs text-neutral-800 rounded-none appearance-none bg-no-repeat"
                  style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%23333333' stroke-width='2'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E")`, backgroundPosition: "right 6px center" }}
                  defaultValue={i === 0 ? "owner" : i === 1 ? "edit" : "view"}
                >
                  <option value="owner">Owner</option>
                  <option value="edit">Can Edit</option>
                  <option value="view">Can View</option>
                </select>
                {i === 1 && (
                  <div className="flex flex-col items-center gap-0.5">
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <button
                            type="button"
                            className="flex h-8 w-8 items-center justify-center rounded-none bg-accent-coral text-white hover:bg-accent-coral-dark"
                            aria-label="Remove"
                          >
                            <X className="h-4 w-4" />
                          </button>
                        </TooltipTrigger>
                        <TooltipContent side="top" className="bg-neutral-800 text-white text-xs rounded-none">
                          Remove
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                    <button
                      type="button"
                      className="flex h-6 w-6 items-center justify-center text-neutral-400 hover:text-neutral-500 rounded-none"
                      aria-label="Drag to reorder"
                    >
                      <GripVertical className="h-4 w-4" />
                    </button>
                  </div>
                )}
              </li>
            ))}
          </ul>
        </div>
      </div>
      <div className="flex items-center justify-between border-t border-neutral-100 px-4 py-3">
        <button
          type="button"
          className="flex items-center gap-2 text-sm text-neutral-800 hover:text-neutral-600 rounded-none"
        >
          <Code className="h-4 w-4 shrink-0" />
          Get embed code
        </button>
        <button
          type="button"
          className="flex items-center gap-2 text-sm text-neutral-800 hover:text-neutral-600 rounded-none"
        >
          <Download className="h-4 w-4 shrink-0" />
          Export
        </button>
      </div>
    </div>
  )
}
