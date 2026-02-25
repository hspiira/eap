import { Plane } from "lucide-react"

export function FlightProgressCard() {
  const progressPercent = 65

  return (
    <div className="border border-[#bfc4c9]/25 bg-white p-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-xl font-bold text-[#5A626A]">LHR</div>
          <div className="text-xs text-[#5A626A]/70">London, UK</div>
          <div className="mt-2 flex flex-wrap gap-1.5">
            <span className="inline-flex items-center border border-[#bfc4c9]/40 bg-[#E6E0D7]/50 px-2 py-0.5 text-xs text-[#5A626A]">
              DEP 08:00
            </span>
            <span className="inline-flex items-center border border-[#bfc4c9]/40 bg-[#E6E0D7]/50 px-2 py-0.5 text-xs text-[#5A626A]">
              GMT+1
            </span>
          </div>
        </div>

        <div className="relative flex min-w-0 flex-1 items-center px-2 pt-6">
          <div className="absolute left-0 right-0 top-6 h-0.5 bg-[#bfc4c9]/40" />
          <div
            className="absolute left-0 top-6 h-0.5 bg-[#5A626A]"
            style={{ width: `${progressPercent}%` }}
          />
          <div
            className="absolute top-6 h-0.5 border-t-2 border-dashed border-[#bfc4c9]/50 bg-white"
            style={{ left: `${progressPercent}%`, right: 0 }}
          />
          <div
            className="relative z-10 -translate-x-1/2"
            style={{ left: `${progressPercent}%` }}
          >
            <Plane className="h-5 w-5 text-[#5A626A]" strokeWidth={2} style={{ transform: "rotate(-45deg)" }} />
          </div>
        </div>

        <div className="text-right">
          <div className="text-xl font-bold text-[#5A626A]">OPO</div>
          <div className="text-xs text-[#5A626A]/70">Porto, PT</div>
          <div className="mt-2 flex flex-wrap justify-end gap-1.5">
            <span className="inline-flex items-center border border-[#bfc4c9]/40 bg-[#E6E0D7]/50 px-2 py-0.5 text-xs text-[#5A626A]">
              ETA 10:15
            </span>
            <span className="inline-flex items-center border border-[#bfc4c9]/40 bg-[#E6E0D7]/50 px-2 py-0.5 text-xs text-[#5A626A]">
              GMT+1
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
