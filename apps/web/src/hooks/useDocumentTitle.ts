/** Sets the browser tab title while the page is mounted, restoring the previous title on unmount. */

import { useEffect } from "react"

export function useDocumentTitle(title: string | null | undefined) {
  useEffect(() => {
    if (!title) return
    const previous = document.title
    document.title = title
    return () => {
      document.title = previous
    }
  }, [title])
}
