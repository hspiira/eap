import { useEffect, useState } from "react"

/**
 * The page the user is reading, as opposed to the one the list started at.
 *
 * Scrolling appends pages without changing the anchor, because the anchor is
 * part of the query key and moving it would throw the appended pages away. So
 * the page the controls show is tracked separately, and resets whenever the
 * anchor moves under it: a jump from the pagination bar, or a filter, search
 * or sort change, all of which start the list again.
 */
export function useVisiblePage(anchorPage: number): [number, (page: number) => void] {
  const [visible, setVisible] = useState(anchorPage)
  useEffect(() => setVisible(anchorPage), [anchorPage])
  return [visible, setVisible]
}
