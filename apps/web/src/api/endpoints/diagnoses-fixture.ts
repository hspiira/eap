/**
 * Two-level diagnosis fixture (D-Tax v2).
 *
 * Mirrors BE shape: DiagnosisTypeWithChildrenResponse → DiagnosisResponse.
 * ICD-10 Chapter V (mental and behavioural disorders) subset.
 */

import type { Diagnosis, DiagnosisTree, DiagnosisType } from '@/types/entities'

const TYPES: (DiagnosisType & { diagnoses: Diagnosis[] })[] = [
  {
    id: 'type-mood',
    code: 'ICD10-F3x',
    name: 'Mood (affective) disorders',
    description: 'ICD-10 Chapter V F30–F39',
    sort_order: 1,
    diagnoses: [
      { id: 'dx-f30', code: 'F30', name: 'Manic episode', type_id: 'type-mood', sort_order: 1 },
      { id: 'dx-f31', code: 'F31', name: 'Bipolar affective disorder', type_id: 'type-mood', sort_order: 2 },
      { id: 'dx-f32', code: 'F32', name: 'Depressive episode', type_id: 'type-mood', sort_order: 3 },
      { id: 'dx-f32-0', code: 'F32.0', name: 'Mild depressive episode', type_id: 'type-mood', sort_order: 4 },
      { id: 'dx-f32-1', code: 'F32.1', name: 'Moderate depressive episode', type_id: 'type-mood', sort_order: 5 },
      { id: 'dx-f32-2', code: 'F32.2', name: 'Severe depressive episode without psychotic symptoms', type_id: 'type-mood', sort_order: 6 },
      { id: 'dx-f33', code: 'F33', name: 'Recurrent depressive disorder', type_id: 'type-mood', sort_order: 7 },
    ],
  },
  {
    id: 'type-anxiety',
    code: 'ICD10-F4x',
    name: 'Anxiety, stress and adjustment disorders',
    description: 'ICD-10 Chapter V F40–F49',
    sort_order: 2,
    diagnoses: [
      { id: 'dx-f40', code: 'F40', name: 'Phobic anxiety disorder', type_id: 'type-anxiety', sort_order: 1 },
      { id: 'dx-f41', code: 'F41', name: 'Other anxiety disorders', type_id: 'type-anxiety', sort_order: 2 },
      { id: 'dx-f41-0', code: 'F41.0', name: 'Panic disorder', type_id: 'type-anxiety', sort_order: 3 },
      { id: 'dx-f41-1', code: 'F41.1', name: 'Generalised anxiety disorder', type_id: 'type-anxiety', sort_order: 4 },
      { id: 'dx-f42', code: 'F42', name: 'Obsessive-compulsive disorder', type_id: 'type-anxiety', sort_order: 5 },
      { id: 'dx-f43', code: 'F43', name: 'Reaction to severe stress and adjustment disorders', type_id: 'type-anxiety', sort_order: 6 },
      { id: 'dx-f43-0', code: 'F43.0', name: 'Acute stress reaction', type_id: 'type-anxiety', sort_order: 7 },
      { id: 'dx-f43-1', code: 'F43.1', name: 'Post-traumatic stress disorder', type_id: 'type-anxiety', sort_order: 8 },
      { id: 'dx-f43-2', code: 'F43.2', name: 'Adjustment disorder', type_id: 'type-anxiety', sort_order: 9 },
    ],
  },
  {
    id: 'type-substance',
    code: 'ICD10-F1x',
    name: 'Substance-use disorders',
    description: 'ICD-10 Chapter V F10–F19',
    sort_order: 3,
    diagnoses: [
      { id: 'dx-f10', code: 'F10', name: 'Alcohol-use disorder', type_id: 'type-substance', sort_order: 1 },
      { id: 'dx-f11', code: 'F11', name: 'Opioid-use disorder', type_id: 'type-substance', sort_order: 2 },
      { id: 'dx-f17', code: 'F17', name: 'Tobacco-use disorder', type_id: 'type-substance', sort_order: 3 },
    ],
  },
  {
    id: 'type-psychosis',
    code: 'ICD10-F2x',
    name: 'Schizophrenia spectrum disorders',
    description: 'ICD-10 Chapter V F20–F29',
    sort_order: 4,
    diagnoses: [
      { id: 'dx-f20', code: 'F20', name: 'Schizophrenia', type_id: 'type-psychosis', sort_order: 1 },
      { id: 'dx-f25', code: 'F25', name: 'Schizoaffective disorder', type_id: 'type-psychosis', sort_order: 2 },
    ],
  },
  {
    id: 'type-personality',
    code: 'ICD10-F6x',
    name: 'Personality disorders',
    description: 'ICD-10 Chapter V F60–F69',
    sort_order: 5,
    diagnoses: [
      { id: 'dx-f60', code: 'F60', name: 'Specific personality disorders', type_id: 'type-personality', sort_order: 1 },
      { id: 'dx-f60-3', code: 'F60.3', name: 'Emotionally unstable personality disorder', type_id: 'type-personality', sort_order: 2 },
    ],
  },
  {
    id: 'type-behavioural',
    code: 'ICD10-F5x',
    name: 'Behavioural syndromes with physiological factors',
    description: 'ICD-10 Chapter V F50–F59',
    sort_order: 6,
    diagnoses: [
      { id: 'dx-f50', code: 'F50', name: 'Eating disorders', type_id: 'type-behavioural', sort_order: 1 },
      { id: 'dx-f51', code: 'F51', name: 'Non-organic sleep disorders', type_id: 'type-behavioural', sort_order: 2 },
    ],
  },
  {
    id: 'type-other',
    code: 'ICD10-Z',
    name: 'Psychosocial factors',
    description: 'ICD-10 Z73 life-management difficulties',
    sort_order: 7,
    diagnoses: [
      { id: 'dx-z73', code: 'Z73', name: 'Problems related to life-management difficulty', type_id: 'type-other', sort_order: 1 },
    ],
  },
]

export function fixtureGetTree(): DiagnosisTree {
  return { types: TYPES }
}

export function fixtureGetTypes(): DiagnosisType[] {
  return TYPES.map(({ diagnoses: _d, ...t }) => t)
}

export function fixtureListDiagnoses(type_code?: string): Diagnosis[] {
  if (type_code) {
    const type = TYPES.find((t) => t.code === type_code)
    return type?.diagnoses ?? []
  }
  return TYPES.flatMap((t) => t.diagnoses)
}
