import { Plus } from "lucide-react"

export function ApexIntroCard() {
  return (
    <div className="rounded-xl border border-neutral-200 bg-surface-lilac-faint p-4 shadow-sm">
      <div className="flex gap-4">
        <div
          className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-surface-lilac text-accent-purple-deep"
          aria-hidden
        >
          <span className="text-lg font-bold">A</span>
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-[15px] text-neutral-800">
            Hello, I am <strong>Apex</strong>, powered by <strong>AX-Prime technology.</strong>
          </p>
          <p className="mt-1.5 text-sm text-neutral-600 leading-relaxed">
            I am a highly advanced AI model designed to handle complex data with ease,
            particularly in the medical field.
          </p>
        </div>
      </div>
      <div className="mt-4 flex items-center gap-3 rounded-full bg-accent-purple-deep px-4 py-2.5">
        <span className="text-xs font-medium text-white shrink-0">0:44</span>
        <div className="flex flex-1 items-center justify-center gap-0.5 py-1 min-h-0">
          {Array.from({ length: 32 }).map((_, i) => (
            <span
              key={i}
              className="w-0.5 shrink-0 rounded-full bg-white/90"
              style={{
                height: `${Math.max(4, 10 + Math.sin(i * 0.6) * 10)}px`,
              }}
            />
          ))}
        </div>
        <button
          type="button"
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-surface-lilac-mid text-white hover:bg-surface-lilac-mid-hover"
          aria-label="Add"
        >
          <Plus className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}
