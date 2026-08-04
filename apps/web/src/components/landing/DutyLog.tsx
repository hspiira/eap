/**
 * Illustrative 24-hour duty log for one programme.
 *
 * Three lanes — sessions, cases, incidents — plotted on a shared hour axis with
 * a marker for the current time. The lone 02:14 incident sitting well outside
 * the working-hours cluster is the point of the whole panel: assistance work
 * does not follow office hours.
 */

const LANES: ReadonlyArray<{
  id: string
  label: string
  color: string
  hours: ReadonlyArray<number>
}> = [
  {
    id: 'sessions',
    label: 'Sessions logged',
    color: 'var(--lp-panel-session)',
    hours: [8.2, 9, 9.7, 10.2, 10.9, 11.4, 12, 13.1, 14, 14.6, 15.3, 16, 16.8, 17.4, 18.2],
  },
  {
    id: 'cases',
    label: 'Cases opened',
    color: 'var(--lp-panel-case)',
    hours: [7.4, 9.3, 11, 12.5, 13.6, 15.1, 17.2, 20.4],
  },
  {
    id: 'incidents',
    label: 'Incidents escalated',
    color: 'var(--lp-panel-incident)',
    hours: [2.2, 16.1],
  },
]

const NOW_HOUR = 14.87

const AXIS_LABELS = [0, 6, 12, 18, 24]

const MOMENTS: ReadonlyArray<{ time: string; title: string; detail: string }> = [
  {
    time: '02:14',
    title: 'Critical incident raised',
    detail: 'Routed to the on-call clinician with the caller’s history attached.',
  },
  {
    time: '09:40',
    title: 'Counsellor assigned',
    detail: 'Matched on language, location, and remaining caseload.',
  },
  {
    time: '16:05',
    title: 'Renewal flagged',
    detail: 'Utilisation against the contract, sixty days before it lapses.',
  },
]

const CHIPS: ReadonlyArray<{ at: number; label: string; stem: string }> = [
  { at: 2.2, label: '02:14 escalated to on-call', stem: 'h-38' },
  { at: 9.3, label: '09:40 counsellor assigned', stem: 'h-28' },
]

const asPercent = (hour: number) => `${(hour / 24) * 100}%`

export function DutyLog() {
  return (
    <figure
      className="lp-rise relative m-0 overflow-hidden rounded-md bg-(--lp-panel) px-5 pt-6 pb-8 text-(--lp-panel-fg) sm:px-8 sm:pt-8 sm:pb-24 md:px-12 md:pt-12 md:pb-28"
      style={{ '--lp-delay': '0.35s' } as React.CSSProperties}
    >
      <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-2">
        <figcaption className="lp-display text-2xl md:text-3xl">
          A day on the programme
        </figcaption>
        <div className="lp-mono flex items-center gap-2 text-[11px] text-(--lp-panel-muted)">
          <span
            className="lp-beacon inline-block size-1.5 rounded-full bg-(--lp-panel-session)"
            aria-hidden
          />
          Illustrative day
        </div>
      </div>

      <p className="sr-only">
        Across an illustrative day, sessions cluster between 08:00 and 18:00,
        cases open steadily from 07:00 to 20:00, and two incidents are escalated
        — one at 02:14, hours outside any working day.
      </p>

      <div className="mt-8 flex flex-col gap-5 md:mt-10 sm:flex-row sm:gap-4" aria-hidden>
        <ul className="flex flex-wrap gap-x-5 gap-y-2 sm:w-44 sm:shrink-0 sm:flex-col sm:gap-4 sm:pt-27 sm:pb-4">
          {LANES.map((lane) => (
            <li
              key={lane.id}
              className="lp-mono flex items-center gap-2 text-[11px] text-(--lp-panel-muted) sm:h-6"
            >
              <span
                className="size-2 shrink-0 rounded-full"
                style={{ backgroundColor: lane.color }}
              />
              {lane.label}
            </li>
          ))}
        </ul>

        <div className="relative flex-1">
          <div className="lp-sky absolute inset-x-0 top-0 bottom-10 rounded-md" />

          {CHIPS.map((chip, index) => (
            <div
              key={chip.at}
              className="lp-rise absolute top-4 hidden -translate-x-1/2 flex-col items-center sm:flex"
              style={
                {
                  left: asPercent(chip.at),
                  '--lp-delay': `${1.6 + index * 0.2}s`,
                } as React.CSSProperties
              }
            >
              <span className="lp-chip lp-mono text-[10px] whitespace-nowrap">
                {chip.label}
              </span>
              <span className={`w-px bg-white/20 ${chip.stem}`} />
            </div>
          ))}

          <div className="flex flex-col gap-4 px-0 pt-6 pb-4 sm:pt-27">
            {LANES.map((lane, laneIndex) => (
              <div key={lane.id} className="relative h-6">
                <div className="absolute inset-x-0 top-1/2 h-px bg-white/8" />
                {lane.hours.map((hour) => (
                  <span
                    key={hour}
                    className="lp-mark absolute top-1/2 size-2 -translate-x-1/2 -translate-y-1/2 rounded-full ring-2 ring-black/30"
                    style={
                      {
                        '--lp-at': asPercent(hour),
                        '--lp-delay': `${0.7 + laneIndex * 0.12 + (hour / 24) * 0.5}s`,
                        backgroundColor: lane.color,
                      } as React.CSSProperties
                    }
                  />
                ))}
              </div>
            ))}
          </div>

          <div
            className="lp-sweep h-px w-full bg-(--lp-panel-line)"
            style={{ '--lp-delay': '0.55s' } as React.CSSProperties}
          />
          <div className="relative h-6">
            {AXIS_LABELS.map((hour) => (
              <span
                key={hour}
                className="lp-mono absolute top-2 -translate-x-1/2 text-[10px] text-(--lp-panel-muted)"
                style={{ left: asPercent(hour) }}
              >
                {String(hour).padStart(2, '0')}
              </span>
            ))}
          </div>

          <div
            className="lp-now lp-rise absolute top-0 bottom-6 w-px bg-(--lp-panel-now)/60"
            style={
              {
                '--lp-at': asPercent(NOW_HOUR),
                '--lp-delay': '1.4s',
              } as React.CSSProperties
            }
          >
            <span className="lp-mono absolute -top-5 left-1/2 -translate-x-1/2 text-[10px] whitespace-nowrap text-(--lp-panel-now)">
              now
            </span>
          </div>
        </div>
      </div>

      <ul className="mt-10 grid gap-6 border-t border-(--lp-panel-line) pt-8 sm:grid-cols-3 md:mt-14">
        {MOMENTS.map((moment, index) => (
          <li
            key={moment.time}
            className="lp-rise grid gap-1.5"
            style={{ '--lp-delay': `${1.5 + index * 0.12}s` } as React.CSSProperties}
          >
            <span className="lp-mono text-[11px] text-(--lp-panel-muted)">
              {moment.time}
            </span>
            <span className="text-[0.9375rem] font-medium">{moment.title}</span>
            <span className="text-sm leading-relaxed text-(--lp-panel-muted)">
              {moment.detail}
            </span>
          </li>
        ))}
      </ul>
    </figure>
  )
}
