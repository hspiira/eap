/**
 * Webhook setup helper for the Survey detail page (Phase 3 #2).
 *
 * Renders a copy-paste-friendly summary of the webhook URL + token plus a step-by-step
 * Google Forms instruction list. Token rotation is exposed as a button so a leaked
 * token can be revoked without re-creating the survey.
 */

import { useState } from "react"

import { Check, Copy, RefreshCcw } from "lucide-react"

import { Button } from "@/components/ui/button"
import { useToast } from "@/contexts/ToastContext"

interface Props {
  webhookUrl: string
  webhookToken: string
  onRotateToken: () => Promise<void> | void
  rotating: boolean
  /** Disables interactive controls when the survey is closed. */
  readOnly?: boolean
}

export function WebhookSetupHelper({ webhookUrl, webhookToken, onRotateToken, rotating, readOnly }: Props) {
  return (
    <section className="border border-fg/20 bg-white p-4 space-y-4">
      <header>
        <h2 className="text-sm font-semibold text-fg">Webhook setup</h2>
        <p className="mt-1 text-xs text-fg/60">
          Configure your survey provider to POST each response to this endpoint with the
          shared secret in the <code>X-Evexia-Token</code> header.
        </p>
      </header>

      <div className="space-y-3">
        <CopyRow label="Webhook URL" value={webhookUrl} />
        <CopyRow label="X-Evexia-Token" value={webhookToken} mask />
      </div>

      <div className="flex justify-end">
        <Button
          type="button"
          variant="secondary"
          size="sm"
          disabled={readOnly || rotating}
          onClick={() => onRotateToken()}
          className="rounded-none border-fg/30 text-fg"
        >
          <RefreshCcw className="mr-2 h-4 w-4" />
          {rotating ? "Rotating…" : "Rotate token"}
        </Button>
      </div>

      <details className="border-t border-fg/10 pt-3">
        <summary className="cursor-pointer text-xs uppercase tracking-wide text-fg/70">
          Google Forms — step-by-step
        </summary>
        <ol className="mt-2 list-decimal pl-5 text-sm text-fg/80 space-y-1">
          <li>
            Open the form, click <strong>Responses → ⋮ → Get email notifications for new responses</strong>{" "}
            and confirm the form is collecting responses.
          </li>
          <li>
            Add the <strong>Email Notifications for Forms</strong> add-on (or your preferred
            webhook bridge — e.g. Zapier, Make).
          </li>
          <li>
            Configure the bridge to <strong>POST</strong> each response as JSON to the URL above.
          </li>
          <li>
            Add a header <strong>X-Evexia-Token</strong> with the secret above. The BE rejects
            any request missing or mismatching this token.
          </li>
          <li>
            Submit a test response. The survey status flips from <em>Draft</em> to{" "}
            <em>Collecting</em> as soon as the first response is accepted.
          </li>
        </ol>
      </details>
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
    } catch {
      showError(`Couldn't copy ${label}`)
    }
  }

  const display = mask && !revealed ? value.replace(/.(?=.{4})/g, "•") : value

  return (
    <div>
      <p className="text-xs uppercase tracking-wide text-fg/60">{label}</p>
      <div className="mt-1 flex items-stretch border border-fg/20">
        <code className="flex-1 truncate bg-neutral-50 px-3 py-2 text-sm text-fg">
          {display}
        </code>
        {mask && (
          <button
            type="button"
            onClick={() => setRevealed((v) => !v)}
            className="border-l border-fg/20 px-3 text-xs uppercase tracking-wide text-fg/70 hover:text-fg"
          >
            {revealed ? "Hide" : "Show"}
          </button>
        )}
        <button
          type="button"
          onClick={handleCopy}
          className="border-l border-fg/20 px-3 text-fg/70 hover:text-fg"
          aria-label={`Copy ${label}`}
        >
          {copied ? <Check className="h-4 w-4 text-primary" /> : <Copy className="h-4 w-4" />}
        </button>
      </div>
    </div>
  )
}
