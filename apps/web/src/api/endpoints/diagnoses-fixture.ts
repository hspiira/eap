/**
 * Hierarchical fixture for the diagnoses combobox (D-Tax UI).
 *
 * ICD-10 Chapter V (mental and behavioral disorders) subset. Replaced by
 * `GET /v1/diagnoses` once BE Phase 2 #1 ships — same shape.
 */

import type { Diagnosis } from '@/types/entities'

interface RawNode {
  id: string
  code: string
  label: string
  parent: string | null
}

const NODES: RawNode[] = [
  // Chapter
  { id: 'icd10-f', code: 'F', label: 'Mental and behavioural disorders', parent: null },

  // F10–F19 — Substance use
  { id: 'icd10-f1x', code: 'F10–F19', label: 'Substance-use disorders', parent: 'icd10-f' },
  { id: 'icd10-f10', code: 'F10', label: 'Alcohol-use disorder', parent: 'icd10-f1x' },
  { id: 'icd10-f11', code: 'F11', label: 'Opioid-use disorder', parent: 'icd10-f1x' },
  { id: 'icd10-f17', code: 'F17', label: 'Tobacco-use disorder', parent: 'icd10-f1x' },

  // F20–F29 — Schizophrenia spectrum
  { id: 'icd10-f2x', code: 'F20–F29', label: 'Schizophrenia and related disorders', parent: 'icd10-f' },
  { id: 'icd10-f20', code: 'F20', label: 'Schizophrenia', parent: 'icd10-f2x' },
  { id: 'icd10-f25', code: 'F25', label: 'Schizoaffective disorder', parent: 'icd10-f2x' },

  // F30–F39 — Mood
  { id: 'icd10-f3x', code: 'F30–F39', label: 'Mood (affective) disorders', parent: 'icd10-f' },
  { id: 'icd10-f31', code: 'F31', label: 'Bipolar affective disorder', parent: 'icd10-f3x' },
  { id: 'icd10-f32', code: 'F32', label: 'Depressive episode', parent: 'icd10-f3x' },
  { id: 'icd10-f32-mild', code: 'F32.0', label: 'Mild depressive episode', parent: 'icd10-f32' },
  { id: 'icd10-f32-mod', code: 'F32.1', label: 'Moderate depressive episode', parent: 'icd10-f32' },
  { id: 'icd10-f32-sev', code: 'F32.2', label: 'Severe depressive episode without psychotic symptoms', parent: 'icd10-f32' },
  { id: 'icd10-f33', code: 'F33', label: 'Recurrent depressive disorder', parent: 'icd10-f3x' },

  // F40–F49 — Anxiety / stress
  { id: 'icd10-f4x', code: 'F40–F49', label: 'Anxiety, stress and somatoform disorders', parent: 'icd10-f' },
  { id: 'icd10-f40', code: 'F40', label: 'Phobic anxiety disorder', parent: 'icd10-f4x' },
  { id: 'icd10-f41', code: 'F41', label: 'Other anxiety disorders', parent: 'icd10-f4x' },
  { id: 'icd10-f41-gad', code: 'F41.1', label: 'Generalised anxiety disorder', parent: 'icd10-f41' },
  { id: 'icd10-f41-panic', code: 'F41.0', label: 'Panic disorder', parent: 'icd10-f41' },
  { id: 'icd10-f42', code: 'F42', label: 'Obsessive-compulsive disorder', parent: 'icd10-f4x' },
  { id: 'icd10-f43', code: 'F43', label: 'Reaction to severe stress and adjustment disorders', parent: 'icd10-f4x' },
  { id: 'icd10-f43-acute', code: 'F43.0', label: 'Acute stress reaction', parent: 'icd10-f43' },
  { id: 'icd10-f43-ptsd', code: 'F43.1', label: 'Post-traumatic stress disorder', parent: 'icd10-f43' },
  { id: 'icd10-f43-adj', code: 'F43.2', label: 'Adjustment disorder', parent: 'icd10-f43' },

  // F50–F59 — Behavioural with physiological
  { id: 'icd10-f5x', code: 'F50–F59', label: 'Behavioural syndromes with physiological factors', parent: 'icd10-f' },
  { id: 'icd10-f50', code: 'F50', label: 'Eating disorders', parent: 'icd10-f5x' },
  { id: 'icd10-f51', code: 'F51', label: 'Non-organic sleep disorders', parent: 'icd10-f5x' },

  // F60–F69 — Personality
  { id: 'icd10-f6x', code: 'F60–F69', label: 'Personality and behaviour disorders', parent: 'icd10-f' },
  { id: 'icd10-f60', code: 'F60', label: 'Specific personality disorders', parent: 'icd10-f6x' },

  // Z73 — life-management
  { id: 'icd10-z73', code: 'Z73', label: 'Problems related to life-management difficulty (work stress, burnout)', parent: null },
]

const NODES_BY_ID: Map<string, RawNode> = new Map(NODES.map((n) => [n.id, n]))

function buildPath(node: RawNode): string {
  const parts: string[] = []
  let cursor: RawNode | undefined = node
  while (cursor) {
    parts.unshift(`${cursor.code} ${cursor.label}`)
    cursor = cursor.parent ? NODES_BY_ID.get(cursor.parent) : undefined
  }
  return parts.join(' / ')
}

function levelOf(node: RawNode): number {
  let depth = 0
  let cursor: RawNode | undefined = node
  while (cursor && cursor.parent) {
    depth += 1
    cursor = NODES_BY_ID.get(cursor.parent)
  }
  return depth
}

const CHILDREN_BY_PARENT = new Map<string | null, RawNode[]>()
for (const n of NODES) {
  const list = CHILDREN_BY_PARENT.get(n.parent) ?? []
  list.push(n)
  CHILDREN_BY_PARENT.set(n.parent, list)
}

export const diagnosesFixture: Diagnosis[] = NODES.map((n) => ({
  id: n.id,
  code: n.code,
  label: n.label,
  parent_id: n.parent,
  level: levelOf(n),
  has_children: (CHILDREN_BY_PARENT.get(n.id)?.length ?? 0) > 0,
  path: buildPath(n),
}))
