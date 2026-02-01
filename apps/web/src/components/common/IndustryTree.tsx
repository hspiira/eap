/**
 * IndustryTree Component
 * Hierarchical tree view for industries with expand/collapse
 */

import { useState, useMemo, useCallback, memo } from 'react'
import { ChevronRight, ChevronDown, Folder, FolderOpen } from 'lucide-react'
import type { Industry } from '@/types/entities'

export interface IndustryTreeProps {
  industries: Industry[]
  onSelect?: (industry: Industry) => void
  selectedId?: string | null
  emptyMessage?: string
  /** Paginate roots: show roots in [offset, offset+limit). Omit to show all. */
  rootOffset?: number
  rootLimit?: number
  className?: string
}

function buildTree(items: Industry[], parentId: string | null = null): Industry[] {
  return items
    .filter((i) => (parentId == null ? !i.parent_id : i.parent_id === parentId))
    .sort((a, b) => (a.name ?? '').localeCompare(b.name ?? ''))
}

export const IndustryTree = memo(function IndustryTree({
  industries,
  onSelect,
  selectedId,
  emptyMessage = 'No industries',
  rootOffset = 0,
  rootLimit,
  className = '',
}: IndustryTreeProps) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set())

  const allRoots = useMemo(() => buildTree(industries, null), [industries])
  const roots = useMemo(() => {
    if (rootLimit == null) return allRoots
    return allRoots.slice(rootOffset, rootOffset + rootLimit)
  }, [allRoots, rootOffset, rootLimit])

  const toggle = useCallback((id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }, [])

  const renderNode = (node: Industry, depth: number) => {
    const children = buildTree(industries, node.id)
    const hasChildren = children.length > 0
    const isExpanded = expanded.has(node.id)
    const isSelected = selectedId === node.id

    const iconCls = isSelected ? 'text-white opacity-90' : 'text-text-muted'
    const codeCls = isSelected ? 'opacity-90' : 'text-text-muted'

    return (
      <div key={node.id} className="select-none">
        <div
          style={{ paddingLeft: `${depth * 14 + 6}px` }}
          className={`flex items-center gap-1.5 py-1 px-1.5 rounded-none cursor-pointer transition-colors text-sm ${
            isSelected ? 'bg-primary text-white' : 'hover:bg-surface-hover'
          }`}
          onClick={() => onSelect?.(node)}
        >
          <button
            type="button"
            aria-label={isExpanded ? 'Collapse' : 'Expand'}
            className="p-0.5 rounded-none hover:bg-surface-hover flex-shrink-0"
            onClick={(e) => {
              e.stopPropagation()
              if (hasChildren) toggle(node.id)
            }}
          >
            {hasChildren ? (
              isExpanded ? (
                <ChevronDown size={14} className={iconCls} />
              ) : (
                <ChevronRight size={14} className={iconCls} />
              )
            ) : (
              <span className="w-3 inline-block" />
            )}
          </button>
          <span className={`flex-shrink-0 ${iconCls}`}>
            {hasChildren && isExpanded ? (
              <FolderOpen size={16} />
            ) : (
              <Folder size={16} />
            )}
          </span>
          <span className="font-medium truncate">{node.name}</span>
          {node.code && (
            <span className={`text-xs truncate ${codeCls}`}>({node.code})</span>
          )}
        </div>
        {hasChildren && isExpanded && (
          <div>
            {children.map((child) => renderNode(child, depth + 1))}
          </div>
        )}
      </div>
    )
  }

  if (roots.length === 0) {
    return (
      <div className={`py-8 text-center text-text-muted text-sm ${className}`}>
        {emptyMessage}
      </div>
    )
  }

  return (
    <div className={`border border-[0.5px] border-border bg-surface ${className}`}>
      {roots.map((node) => renderNode(node, 0))}
    </div>
  )
})
