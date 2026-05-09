import { type ThemePreference,useTheme } from '@/contexts/ThemeContext'

const THEME_OPTIONS: ReadonlyArray<{ value: ThemePreference; label: string }> = [
  { value: 'light', label: 'Light' },
  { value: 'dark', label: 'Dark' },
  { value: 'system', label: 'System' },
]

const DENSITY_OPTIONS = ['compact', 'comfortable'] as const
type Density = (typeof DENSITY_OPTIONS)[number]

interface GalleryControlsProps {
  density: Density
  onDensityChange: (density: Density) => void
}

export function GalleryControls({ density, onDensityChange }: GalleryControlsProps) {
  const { preference, setPreference } = useTheme()

  return (
    <div className="sticky top-0 z-10 -mx-6 mb-6 flex flex-wrap items-center justify-between gap-3 border-b border-border bg-bg/95 px-6 py-3 backdrop-blur">
      <div className="flex items-baseline gap-3">
        <h1 className="text-base font-semibold text-fg">Component gallery</h1>
        <span className="font-mono text-xs text-fg-subtle">/design</span>
      </div>
      <div className="flex items-center gap-4">
        <SegmentedControl
          label="Theme"
          value={preference}
          options={THEME_OPTIONS}
          onChange={(v) => setPreference(v as ThemePreference)}
        />
        <SegmentedControl
          label="Density"
          value={density}
          options={DENSITY_OPTIONS.map((d) => ({ value: d, label: cap(d) }))}
          onChange={(v) => onDensityChange(v as Density)}
        />
      </div>
    </div>
  )
}

interface SegmentedControlProps<T extends string> {
  label: string
  value: T
  options: ReadonlyArray<{ value: T; label: string }>
  onChange: (value: T) => void
}

function SegmentedControl<T extends string>({
  label,
  value,
  options,
  onChange,
}: SegmentedControlProps<T>) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs font-medium uppercase tracking-wide text-fg-muted">
        {label}
      </span>
      <div
        role="radiogroup"
        aria-label={label}
        className="inline-flex rounded-sm border border-border bg-surface p-0.5"
      >
        {options.map((opt) => {
          const selected = opt.value === value
          return (
            <button
              key={opt.value}
              type="button"
              role="radio"
              aria-checked={selected}
              onClick={() => onChange(opt.value)}
              className={
                'rounded-sm px-2.5 py-1 text-xs font-medium transition-colors ' +
                (selected
                  ? 'bg-brand text-fg-on-brand'
                  : 'text-fg-muted hover:text-fg')
              }
            >
              {opt.label}
            </button>
          )
        })}
      </div>
    </div>
  )
}

function cap(s: string) {
  return s.charAt(0).toUpperCase() + s.slice(1)
}
