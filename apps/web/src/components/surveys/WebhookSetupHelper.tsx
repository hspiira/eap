/**
 * Webhook setup helper for the Survey detail page (Phase 3 #2).
 *
 * The URL is derived from the mounted route rather than read off the campaign:
 * the API returns no webhook URL, and no secret either. The secret is set when
 * the campaign is created and is deliberately never returned again, so this
 * says so instead of rendering an undefined value (MODULES_REPAIR_PLAN API-01;
 * SUR-01 adds the server-generated, copy-once secret).
 */

import { useState } from "react"

import { Check, Copy } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { useToast } from "@/contexts/ToastContext"

interface Props {
  campaignId: string
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(
  /\/$/,
  "",
)

export function WebhookSetupHelper({ campaignId }: Props) {
  const webhookUrl = `${API_BASE_URL}/survey-campaigns/${campaignId}/webhook`
  return (
    <section className="space-y-4 rounded-sm border border-fg/10 bg-surface p-4">
      <header>
        <h2 className="text-sm font-semibold text-fg">Webhook setup</h2>
        <p className="mt-1 text-xs text-fg/60">
          Configure your survey provider to POST each response to this endpoint, signed with the
          campaign's secret in the <code>X-Webhook-Signature</code> header.
        </p>
      </header>

      <div className="space-y-3">
        <CopyRow label="Webhook URL" value={webhookUrl} />
        <p className="rounded-sm border border-fg/10 bg-bg px-3 py-2 text-xs text-fg/65">
          The signing secret was set when this campaign was created and is not retrievable. If it
          has been lost, create a new campaign.
        </p>
      </div>

      <Collapsible className="border-t border-fg/10 pt-3">
        <CollapsibleTrigger asChild>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-auto p-0 text-[11px] font-semibold tracking-wide text-fg/70 hover:bg-transparent hover:text-fg"
          >
            Google Forms: step-by-step
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <ol className="mt-2 list-decimal pl-5 text-sm text-fg/80 space-y-1">
            <li>
              Open the form, click{" "}
              <strong>Responses → ⋮ → Get email notifications for new responses</strong> and confirm
              the form is collecting responses.
            </li>
            <li>
              Add the <strong>Email Notifications for Forms</strong> add-on (or your preferred
              webhook bridge, e.g. Zapier, Make).
            </li>
            <li>
              Configure the bridge to <strong>POST</strong> each response as JSON to the URL above.
            </li>
            <li>
              Sign each request body with the campaign's secret and send the digest in an{" "}
              <strong>X-Webhook-Signature</strong> header. The BE rejects any request whose
              signature is missing or does not match.
            </li>
            <li>
              Activate the campaign, then submit a test response. Accepted deliveries increment the
              response count on this page.
            </li>
          </ol>
        </CollapsibleContent>
      </Collapsible>
    </section>
  )
}

function CopyRow({ label, value, mask }: { label: string; value: string; mask?: boolean }) {
  const { showSuccess, showError } = useToast()
  const [copied, setCopied] = useState(false)
  const [revealed, setRevealed] = useState(!mask)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(value)
      setCopied(true)
      showSuccess(`${label} copied`)
      setTimeout(() => setCopied(false), 2000)
    } catch (_err) {
      showError(`Couldn't copy ${label}`)
    }
  }

  const display = mask && !revealed ? value.replace(/.(?=.{4})/g, "•") : value

  return (
    <div>
      <p className="text-[11px] font-semibold tracking-wide text-fg-muted">{label}</p>
      <div className="mt-1 flex items-stretch overflow-hidden rounded-sm border border-fg/15">
        <code className="flex-1 truncate bg-bg px-3 py-2 text-xs text-fg">{display}</code>
        {mask && (
          <Button
            type="button"
            variant="ghost"
            onClick={() => setRevealed((v) => !v)}
            className="h-auto rounded-none border-l border-fg/15 px-3 text-[10px] font-semibold tracking-wide text-fg/70"
          >
            {revealed ? "Hide" : "Show"}
          </Button>
        )}
        <Button
          type="button"
          variant="ghost"
          onClick={handleCopy}
          className="size-9 rounded-none border-l border-fg/15 p-0 text-fg/70"
          aria-label={`Copy ${label}`}
        >
          {copied ? <Check className="size-4 text-primary" /> : <Copy className="size-4" />}
        </Button>
      </div>
    </div>
  )
}
