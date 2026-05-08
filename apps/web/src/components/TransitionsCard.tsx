import { useState } from "react"

import {
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  Ban,
  Copy,
  Maximize2,
  MoveHorizontal,
  Plus,
  Send,
  Sparkles,
  Square,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { cn } from "@/lib/utils"

const TRANSITION_TYPES = [
  { id: "none", label: "None", icon: Ban },
  { id: "dissolve", label: "Dissolve", icon: Copy },
  { id: "push", label: "Push", icon: MoveHorizontal },
  { id: "slide", label: "Slide", icon: ArrowRight },
  { id: "scale", label: "Scale", icon: Maximize2 },
  { id: "fade", label: "Fade", icon: Square },
] as const

type TransitionId = (typeof TRANSITION_TYPES)[number]["id"]

const APPLY_OPTIONS = ["Both", "On Enter", "On Exit"] as const
type ApplyOption = (typeof APPLY_OPTIONS)[number]

const DIRECTIONS = [
  { id: "right", label: "Right", icon: ArrowRight },
  { id: "left", label: "Left", icon: ArrowLeft },
  { id: "up", label: "Up", icon: ArrowUp },
  { id: "down", label: "Down", icon: ArrowDown },
] as const

type DirectionId = (typeof DIRECTIONS)[number]["id"]

const QUICK_PROMPTS = [
  "Make it fast",
  "Smooth slide from top-left to bottom-right",
] as const

export function TransitionsCard() {
  const [transition, setTransition] = useState<TransitionId>("push")
  const [apply, setApply] = useState<ApplyOption>("Both")
  const [direction, setDirection] = useState<DirectionId>("right")
  const [prompt, setPrompt] = useState("")

  return (
    <Card className="rounded-md">
      <CardHeader className="flex-row items-center gap-2 space-y-0 border-b border-border-subtle p-3">
        <Sparkles className="size-4 text-primary" aria-hidden />
        <CardTitle className="text-sm font-semibold text-fg">
          Transitions
        </CardTitle>
      </CardHeader>

      <CardContent className="grid gap-4 p-4">
        <div className="flex flex-wrap items-center gap-2">
          {TRANSITION_TYPES.map(({ id, label, icon: Icon }) => {
            const selected = id === transition
            return (
              <button
                key={id}
                type="button"
                aria-pressed={selected}
                onClick={() => setTransition(id)}
                className={cn(
                  "inline-flex items-center gap-2 rounded-sm border px-3 py-1.5 text-sm font-medium transition-colors",
                  selected
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-border-subtle bg-surface text-fg hover:bg-surface-hover",
                )}
              >
                <Icon className="size-3.5" />
                {label}
              </button>
            )
          })}
          <Button
            variant="outline"
            size="icon"
            aria-label="More transitions"
            className="border-dashed text-fg-subtle"
          >
            <Plus className="size-3.5" />
          </Button>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div
            role="radiogroup"
            aria-label="Apply on"
            className="inline-flex rounded-sm border border-border-subtle bg-surface p-0.5"
          >
            {APPLY_OPTIONS.map((opt) => {
              const selected = opt === apply
              return (
                <button
                  key={opt}
                  type="button"
                  role="radio"
                  aria-checked={selected}
                  onClick={() => setApply(opt)}
                  className={cn(
                    "rounded-sm px-2.5 py-1 text-xs font-medium transition-colors",
                    selected
                      ? "bg-primary text-primary-foreground"
                      : "text-fg-muted hover:text-fg",
                  )}
                >
                  {opt}
                </button>
              )
            })}
          </div>
          <div className="inline-flex rounded-sm border border-border-subtle bg-surface p-0.5">
            {DIRECTIONS.map(({ id, label, icon: Icon }) => {
              const selected = id === direction
              return (
                <button
                  key={id}
                  type="button"
                  aria-pressed={selected}
                  aria-label={label}
                  onClick={() => setDirection(id)}
                  className={cn(
                    "rounded-sm p-1.5 transition-colors",
                    selected
                      ? "bg-primary text-primary-foreground"
                      : "text-fg-muted hover:text-fg",
                  )}
                >
                  <Icon className="size-3.5" />
                </button>
              )
            })}
          </div>
          <span className="text-xs text-fg-muted">Apply to all scenes</span>
        </div>

        <div className="grid gap-2 rounded-sm border border-border-subtle bg-surface p-3">
          <div className="flex flex-wrap gap-2">
            {QUICK_PROMPTS.map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => setPrompt(p)}
                className="rounded-sm border border-border-subtle bg-bg px-2.5 py-1 text-xs text-fg-muted transition-colors hover:bg-surface-hover hover:text-fg"
              >
                {p}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Describe a transition…"
              aria-label="Transition prompt"
              className="flex-1 rounded-sm border border-border-subtle bg-bg px-2.5 py-1.5 text-sm text-fg outline-none placeholder:text-fg-subtle focus-visible:ring-2 focus-visible:ring-ring"
            />
            <Button
              size="icon"
              aria-label="Submit prompt"
              disabled={prompt.trim().length === 0}
            >
              <Send className="size-3.5" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
