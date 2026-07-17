import * as React from "react"

import { ArrowLeft, RotateCw } from "lucide-react"

import { EmptyState } from "@/components/common/EmptyState"
import { PageShell } from "@/components/common/PageShell"
import { DetailSkeleton } from "@/components/common/PageSkeletons"
import { Button } from "@/components/ui/button"
import { isNotFound, normalizeErrorMessage } from "@/lib/errors"

interface DetailStateProps {
  icon: React.ElementType
  /** Breadcrumb trail without the trailing entity segment, e.g. "People · Persons". */
  breadcrumb: string
  /** Singular, lowercase entity noun used in copy, e.g. "person". */
  entity: string
  backTo: () => void
  backLabel: string
}

export function DetailLoading({ icon, breadcrumb }: Pick<DetailStateProps, "icon" | "breadcrumb">) {
  return (
    <PageShell icon={icon} breadcrumb={`${breadcrumb} · …`}>
      <div className="min-h-0 flex-1 overflow-auto p-5">
        <DetailSkeleton />
      </div>
    </PageShell>
  )
}

export function DetailNotFound({
  icon,
  breadcrumb,
  entity,
  backTo,
  backLabel,
}: DetailStateProps) {
  return (
    <PageShell icon={icon} breadcrumb={`${breadcrumb} · Not found`}>
      <EmptyState
        icon={icon}
        title={`${entity.charAt(0).toUpperCase()}${entity.slice(1)} not found`}
        description="It may have been archived, or never existed."
        action={
          <Button variant="outline" size="sm" className="gap-1.5" onClick={backTo}>
            <ArrowLeft className="size-4" />
            {backLabel}
          </Button>
        }
      />
    </PageShell>
  )
}

interface DetailErrorProps extends DetailStateProps {
  error: unknown
  onRetry: () => void
}

export function DetailError({
  icon,
  breadcrumb,
  entity,
  error,
  onRetry,
  backTo,
  backLabel,
}: DetailErrorProps) {
  return (
    <PageShell icon={icon} breadcrumb={`${breadcrumb} · Error`}>
      <EmptyState
        icon={icon}
        title={`Couldn't load this ${entity}`}
        description={normalizeErrorMessage(error, "Something went wrong. Please try again.")}
        action={
          <div className="flex items-center gap-2">
            <Button size="sm" className="gap-1.5" onClick={onRetry}>
              <RotateCw className="size-4" />
              Try again
            </Button>
            <Button variant="outline" size="sm" className="gap-1.5" onClick={backTo}>
              <ArrowLeft className="size-4" />
              {backLabel}
            </Button>
          </div>
        }
      />
    </PageShell>
  )
}

interface DetailQueryLike {
  isPending: boolean
  isError: boolean
  error: unknown
  data: unknown
  refetch: () => void
}

/**
 * Loading / not-found / failed states for a detail query; `null` when the caller
 * should render the entity. Only a 404 means missing — anything else is retryable.
 */
export function renderDetailState(
  query: DetailQueryLike,
  props: DetailStateProps,
): React.ReactElement | null {
  if (query.isPending) {
    return <DetailLoading icon={props.icon} breadcrumb={props.breadcrumb} />
  }
  if (query.isError) {
    return isNotFound(query.error) ? (
      <DetailNotFound {...props} />
    ) : (
      <DetailError {...props} error={query.error} onRetry={() => query.refetch()} />
    )
  }
  if (!query.data) {
    return <DetailNotFound {...props} />
  }
  return null
}
