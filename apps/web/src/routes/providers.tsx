import { createFileRoute } from "@tanstack/react-router"

import { AuthedLayout } from "@/components/common/AuthedLayout"

export const Route = createFileRoute("/providers")({ component: AuthedLayout })
