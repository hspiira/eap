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
    <div className="flex flex-col border border-[#bfc4c9]/30 bg-[#E6E0D7] rounded-none overflow-hidden">
      <div className="flex flex-wrap items-center gap-1 p-3 border-b border-[#5A626A]/20">
        {toolbarIcons.map(({ icon: Icon, label }) => (
          <button
            key={label}
            type="button"
            className="p-2 text-[#5A626A] hover:bg-[#5A626A]/10 rounded-none transition-colors"
            aria-label={label}
          >
            <Icon className="h-4 w-4" />
          </button>
        ))}
        <button
          type="button"
          className="inline-flex items-center gap-1.5 px-3 py-2 bg-[#5A626A]/15 text-[#5A626A] border border-[#5A626A] font-medium rounded-none"
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
                "inline-flex items-center gap-2 px-3 py-2 border bg-white text-[#5A626A] rounded-none text-sm font-medium transition-colors",
                id === "push"
                  ? "border-[#5A626A] ring-1 ring-[#5A626A]"
                  : "border-[#bfc4c9]/40 hover:border-[#5A626A]/50"
              )}
            >
              <Icon className="h-3.5 w-3.5" />
              {label}
            </button>
          ))}
          <button
            type="button"
            className="w-9 h-9 border border-dashed border-[#bfc4c9]/50 bg-white/50 text-[#5A626A]/50 hover:border-[#5A626A]/50 rounded-none"
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
                    ? "bg-[#5A626A]/15 border-[#5A626A]/30 text-[#5A626A]"
                    : "bg-white border-[#bfc4c9]/40 text-[#5A626A] hover:border-[#5A626A]/50"
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
                    ? "bg-[#5A626A] text-white border-[#5A626A]"
                    : "bg-white border-[#bfc4c9]/40 text-[#5A626A] hover:border-[#5A626A]/50"
                )}
                aria-label={["Right", "Left", "Up", "Down"][i]}
              >
                <Icon className="h-3.5 w-3.5" />
              </button>
            ))}
          </div>
          <span className="text-sm text-[#5A626A]/80">Apply All Scenes</span>
        </div>

        <div className="flex flex-col gap-2 p-3 bg-white border border-[#bfc4c9]/30 rounded-none">
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="px-3 py-1.5 bg-[#E6E0D7] border border-[#bfc4c9]/30 text-[#5A626A] text-sm rounded-none hover:bg-[#E6E0D7]/80"
            >
              Make it fast
            </button>
            <button
              type="button"
              className="px-3 py-1.5 bg-[#E6E0D7] border border-[#bfc4c9]/30 text-[#5A626A] text-sm rounded-none hover:bg-[#E6E0D7]/80"
            >
              Add a Smooth slide from top left corner to bottom right corner
            </button>
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Type your prompt here..."
              className="flex-1 min-w-0 px-3 py-2 border border-[#bfc4c9]/40 bg-[#fafafa] text-[#5A626A] placeholder:text-[#5A626A]/50 text-sm rounded-none focus:outline-none focus:border-[#5A626A]/60"
            />
            <button
              type="button"
              className="p-2 bg-[#5A626A] text-white border border-[#5A626A] rounded-none hover:opacity-90 transition-opacity"
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
