import {
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  Ban,
  Captions,
  Copy,
  Layers,
  LayoutGrid,
  Maximize2,
  MoveHorizontal,
  Music,
  Palette,
  Play,
  PlusCircle,
  Radio,
  Sparkles,
  Square,
  Type,
  User,
} from "lucide-react"

import { cn } from "@/lib/utils"

const toolbarIcons = [
  { icon: Type, label: "Text" },
  { icon: LayoutGrid, label: "Grid" },
  { icon: Radio, label: "Audio" },
  { icon: Play, label: "Video" },
  { icon: PlusCircle, label: "Add" },
  { icon: Captions, label: "Captions" },
  { icon: Type, label: "Font" },
  { icon: Layers, label: "Layers" },
  { icon: User, label: "Profile" },
  { icon: Music, label: "Music" },
  { icon: Palette, label: "Color" },
]

const transitionTypes = [
  { id: "none", label: "None", icon: Ban },
  { id: "dissolve", label: "Dissolve", icon: Copy },
  { id: "push", label: "Push", icon: MoveHorizontal },
  { id: "slide", label: "Slide", icon: ArrowRight },
  { id: "scale", label: "Scale", icon: Maximize2 },
  { id: "fade", label: "Fade", icon: Square },
] as const

const applyOptions = ["Both", "On Enter", "On Exit"] as const

const directionIcons = [ArrowRight, ArrowLeft, ArrowUp, ArrowDown]

export function TransitionsCard() {
  return (
    <div className="flex flex-col border border-border/30 bg-surface rounded-none overflow-hidden">
      <div className="flex flex-wrap items-center gap-1 p-3 border-b border-fg/20">
        {toolbarIcons.map(({ icon: Icon, label }) => (
          <button
            key={label}
            type="button"
            className="p-2 text-fg hover:bg-fg/10 rounded-none transition-colors"
            aria-label={label}
          >
            <Icon className="h-4 w-4" />
          </button>
        ))}
        <button
          type="button"
          className="inline-flex items-center gap-1.5 px-3 py-2 bg-fg/15 text-fg border border-fg font-medium rounded-none"
          aria-label="Transitions"
        >
          <Sparkles className="h-4 w-4" />
          <span>Transitions</span>
        </button>
      </div>

      <div className="flex flex-col gap-4 p-4">
        <div className="flex flex-wrap items-center gap-2">
          {transitionTypes.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type="button"
              className={cn(
                "inline-flex items-center gap-2 px-3 py-2 border bg-white text-fg rounded-none text-sm font-medium transition-colors",
                id === "push"
                  ? "border-fg ring-1 ring-ink"
                  : "border-border/40 hover:border-fg/50"
              )}
            >
              <Icon className="h-3.5 w-3.5" />
              {label}
            </button>
          ))}
          <button
            type="button"
            className="w-9 h-9 border border-dashed border-border/50 bg-white/50 text-fg/50 hover:border-fg/50 rounded-none"
            aria-label="More"
          />
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1">
            {applyOptions.map((opt) => (
              <button
                key={opt}
                type="button"
                className={cn(
                  "px-3 py-2 border text-sm font-medium rounded-none transition-colors",
                  opt === "Both"
                    ? "bg-fg/15 border-fg/30 text-fg"
                    : "bg-white border-border/40 text-fg hover:border-fg/50"
                )}
              >
                {opt}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-1">
            {directionIcons.map((Icon, i) => (
              <button
                key={i}
                type="button"
                className={cn(
                  "p-2 border rounded-none transition-colors",
                  i === 0
                    ? "bg-fg text-white border-fg"
                    : "bg-white border-border/40 text-fg hover:border-fg/50"
                )}
                aria-label={["Right", "Left", "Up", "Down"][i]}
              >
                <Icon className="h-3.5 w-3.5" />
              </button>
            ))}
          </div>
          <span className="text-sm text-fg/80">Apply All Scenes</span>
        </div>

        <div className="flex flex-col gap-2 p-3 bg-white border border-border/30 rounded-none">
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="px-3 py-1.5 bg-surface border border-border/30 text-fg text-sm rounded-none hover:bg-surface/80"
            >
              Make it fast
            </button>
            <button
              type="button"
              className="px-3 py-1.5 bg-surface border border-border/30 text-fg text-sm rounded-none hover:bg-surface/80"
            >
              Add a Smooth slide from top left corner to bottom right corner
            </button>
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Type your prompt here..."
              className="flex-1 min-w-0 px-3 py-2 border border-border/40 bg-neutral-50 text-fg placeholder:text-fg/50 text-sm rounded-none focus:outline-none focus:border-fg/60"
            />
            <button
              type="button"
              className="p-2 bg-fg text-white border border-fg rounded-none hover:opacity-90 transition-opacity"
              aria-label="Submit prompt"
            >
              <ArrowUp className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
