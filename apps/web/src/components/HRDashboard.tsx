import { BarChart3, ChevronRight, FileText, Mail, Receipt, RefreshCw, User } from "lucide-react"

import { ChartAreaInteractive } from "@/components/ChartAreaInteractive"
import { cn } from "@/lib/utils"

function Card({ title, link, children, className }: { title: string; link?: string; children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("flex flex-col border border-[#bfc4c9]/25 bg-white p-4", className)}>
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-[#5A626A]">{title}</h3>
        {link && (
          <button type="button" className="text-xs text-[#5A626A]/70 hover:text-natural">
            {link} <ChevronRight className="inline h-3 w-3" />
          </button>
        )}
      </div>
      {children}
    </div>
  )
}

export function HRDashboard() {
  return (
    <div className="mx-auto max-w-6xl space-y-4 p-4">
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card title="This Week's Data" link="This week's count >">
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-[#5A626A]">3,320</span>
            <span className="text-sm font-medium text-[#b85c4a]">+224</span>
          </div>
          <div className="my-3 flex items-center gap-4">
            <div
              className="h-24 w-24 shrink-0 rounded-full border-4 border-[#E6E0D7]"
              style={{
                background: `conic-gradient(#5A626A 0deg 260deg, #D0B5B3 260deg 320deg, #e5e5e5 320deg 350deg, #bfc4c9 350deg 360deg)`,
              }}
            />
            <div className="min-w-0 flex-1 space-y-1 text-xs text-[#5A626A]/90">
              <div className="flex justify-between"><span>Positive</span><span className="font-medium">2,459</span></div>
              <div className="flex justify-between"><span>Late</span><span className="font-medium">280</span></div>
              <div className="flex justify-between"><span>Tech</span><span className="font-medium">56</span></div>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="border border-[#bfc4c9]/20 bg-[#fafafa] p-2">
              <div className="text-lg font-bold text-[#5A626A]">23</div>
              <div className="text-[10px] text-[#5A626A]/70">This week's approval</div>
              <div className="text-[10px] text-[#5A626A]/60">Approved 2 · Pending 2</div>
            </div>
            <div className="border border-[#bfc4c9]/20 bg-[#fafafa] p-2">
              <div className="text-lg font-bold text-[#5A626A]">14</div>
              <div className="text-[10px] text-[#5A626A]/70">Promotion</div>
              <div className="text-[10px] text-[#5A626A]/60">Promoted 2 · Pending 2</div>
            </div>
            <div className="border border-[#bfc4c9]/20 bg-[#fafafa] p-2">
              <div className="text-lg font-bold text-[#5A626A]">17</div>
              <div className="text-[10px] text-[#5A626A]/70">HR</div>
              <div className="text-[10px] text-[#5A626A]/60">Onboard +4 · Left +4</div>
            </div>
          </div>
        </Card>

        <Card title="Today's To-Do" link="View all >">
          <div className="mb-3 flex items-center justify-between rounded-none border border-[#bfc4c9]/30 bg-[#fafafa] px-2 py-1">
            <button type="button" className="p-1 text-[#5A626A]/70">←</button>
            <span className="text-xs text-[#5A626A]">2022/06 19 20 21 22 23 24 25</span>
            <button type="button" className="p-1 text-[#5A626A]/70">→</button>
          </div>
          <ul className="space-y-2">
            {["9:00 New employee onboarding", "14:00 Internal HR meeting", "15:00 Approval reimbursement review"].map((item, i) => (
              <li key={i} className="flex gap-2 text-sm text-[#5A626A]">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[#5A626A]" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </Card>

        <Card title="Quick access">
          <div className="flex items-center gap-3">
            <div className="h-12 w-12 shrink-0 rounded-none bg-[#D0B5B3] flex items-center justify-center text-lg font-bold text-white">Z</div>
            <div>
              <p className="text-sm font-medium text-[#5A626A]">Good morning!</p>
              <p className="text-xs text-[#5A626A]/70">Manager · Admin: All company</p>
            </div>
          </div>
          <div className="mt-3 flex gap-2">
            {["Manager", "Admin"].map((role, i) => (
              <div key={i} className="flex flex-col items-center gap-1">
                <div className="h-10 w-10 rounded-none bg-[#E6E0D7] flex items-center justify-center text-xs font-medium text-[#5A626A]">
                  {role.slice(0, 1)}
                </div>
                <span className="text-[10px] text-[#5A626A]/70">{role}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card title="Common Applications" link="All applications >">
          <div className="grid grid-cols-3 gap-3">
            {[
              { icon: Mail, label: "Mail" },
              { icon: FileText, label: "Questionnaire" },
              { icon: BarChart3, label: "JIRA" },
              { icon: BarChart3, label: "Performance" },
              { icon: User, label: "HR" },
              { icon: Receipt, label: "Payslip" },
            ].map(({ icon: Icon, label }, i) => (
              <button key={i} type="button" className="flex flex-col items-center gap-1 rounded-none border border-[#bfc4c9]/20 bg-[#fafafa] p-3 hover:bg-[#E6E0D7]">
                <Icon className="h-6 w-6 text-[#5A626A]" />
                <span className="text-xs text-[#5A626A]">{label}</span>
              </button>
            ))}
          </div>
        </Card>

        <Card title="Help Center" link="View all >">
          <div className="flex gap-4 border-b border-[#bfc4c9]/20 pb-2">
            <button type="button" className="text-xs font-medium text-[#5A626A] border-b-2 border-[#5A626A] pb-0.5">Common questions</button>
            <button type="button" className="text-xs text-[#5A626A]/70 hover:text-[#5A626A]">HR Management</button>
          </div>
          <ul className="mt-2 space-y-1.5 text-xs text-[#5A626A]/90">
            {[
              "New employee onboarding process and documents",
              "Contract, archives and company document entry",
              "Creating to-dos and related manuals",
              "Confidentiality and customer confidentiality solutions",
              "Smart collaborative office operations manual",
            ].map((text, i) => (
              <li key={i}>
                <button type="button" className="text-left hover:text-natural">{text}</button>
              </li>
            ))}
          </ul>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card title="Employee Data" link="View details >">
          <div className="mb-3 text-3xl font-bold text-[#5A626A]">3,345</div>
          <p className="mb-3 text-xs text-[#5A626A]/70">Total employees</p>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {[
              { label: "Full-time", value: "2,830" },
              { label: "Intern", value: "46" },
              { label: "Probation", value: "32" },
              { label: "Outsource", value: "80" },
              { label: "Official", value: "2,710" },
              { label: "Resignation", value: "18" },
              { label: "Vacant", value: "5" },
            ].map(({ label, value }) => (
              <div key={label} className="flex justify-between border-b border-[#bfc4c9]/15 py-1">
                <span className="text-[#5A626A]/80">{label}</span>
                <span className="font-medium text-[#5A626A]">{value}</span>
              </div>
            ))}
          </div>
        </Card>

        <div className="flex flex-col gap-4 lg:col-span-2">
          <Card title="Alerts">
            <div className="flex items-start gap-3">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-none bg-[#D0B5B3] text-lg font-bold text-white">40</div>
              <ul className="min-w-0 flex-1 space-y-1.5 text-xs text-[#5A626A]">
                <li><span className="font-medium text-[#b85c4a]">13</span> employees with contract expiring soon</li>
                <li><span className="font-medium text-[#b85c4a]">23</span> employees missing emergency contact</li>
                <li><span className="font-medium text-[#b85c4a]">7</span> employees absent 1 day in last 7 days</li>
              </ul>
            </div>
          </Card>

          <Card title="Announcements" link="View all >">
            <ul className="space-y-2 text-xs text-[#5A626A]">
              {[
                "6-20 Knowledge base and document organization notice",
                "6-19 Field management and field staff welfare plan update",
                "6-18 Empower all staff, precise decisions, efficient management",
              ].map((text, i) => (
                <li key={i} className="border-b border-[#bfc4c9]/15 pb-2 last:border-0 last:pb-0">
                  <button type="button" className="text-left hover:text-natural">{text}</button>
                </li>
              ))}
            </ul>
          </Card>
        </div>
      </div>

      <Card title="Employee Changes" link="View all >">
        <div className="mb-4 flex flex-wrap gap-2">
          <button type="button" className="flex items-center gap-1 rounded-none border border-[#bfc4c9]/40 bg-[#fafafa] px-2 py-1 text-xs text-[#5A626A]">
            <RefreshCw className="h-3 w-3" /> Selection: All company
          </button>
          <button type="button" className="flex items-center gap-1 rounded-none border border-[#bfc4c9]/40 bg-[#fafafa] px-2 py-1 text-xs text-[#5A626A]">
            By entry date
          </button>
        </div>
        <div className="mb-4 grid grid-cols-4 gap-4">
          {[
            { label: "Onboarded", value: "639" },
            { label: "Left", value: "320" },
            { label: "New hires", value: "178" },
            { label: "Removed", value: "245" },
          ].map(({ label, value }) => (
            <div key={label} className="text-center">
              <div className="text-2xl font-bold text-[#5A626A]">{value}</div>
              <div className="text-xs text-[#5A626A]/70">{label}</div>
            </div>
          ))}
        </div>
        <div className="mb-4 rounded-none border border-[#bfc4c9]/25 bg-white p-4">
          <ChartAreaInteractive />
        </div>
        <div className="flex gap-4 border-t border-[#bfc4c9]/20 pt-3">
          <button type="button" className="text-xs font-medium text-[#5A626A] border-b-2 border-[#5A626A] pb-0.5">New hires</button>
          <button type="button" className="text-xs text-[#5A626A]/70 hover:text-[#5A626A]">Removed</button>
        </div>
        <ul className="mt-2 space-y-2">
          {["Ding Shi, Specialist, 06/23 onboard", "Li Ming, Engineer, 06/22 onboard", "Wang Fang, Analyst, 06/21 onboard"].map((entry, i) => (
            <li key={i} className="flex items-center gap-2 text-sm text-[#5A626A]">
              <div className="h-8 w-8 shrink-0 rounded-none bg-[#E6E0D7] flex items-center justify-center text-xs font-medium text-[#5A626A]">
                {entry.slice(0, 1)}
              </div>
              <span>{entry}</span>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  )
}
