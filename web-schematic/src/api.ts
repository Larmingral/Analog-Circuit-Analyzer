import type { AnalysisJob, DeviceDefinition, Diagnostic, SchematicDocument, SlicapSchematicDocument } from './types'

const API = import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8000/api/v1'
const OFFICIAL_SYMBOLS = import.meta.env.VITE_SCHEMATIC_MODE !== 'legacy'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    ...init,
  })
  if (!response.ok) {
    const message = await response.text()
    throw new Error(`${response.status}: ${message}`)
  }
  return response.json() as Promise<T>
}

export async function fetchCatalog(): Promise<Record<string, DeviceDefinition>> {
  const response = await request<{ devices: Record<string, DeviceDefinition> }>('/catalog/devices')
  const origin = new URL(API).origin
  return Object.fromEntries(Object.entries(response.devices).map(([name, definition]) => [
    name,
    {
      ...definition,
      symbol_url: OFFICIAL_SYMBOLS && definition.symbol_url
        ? new URL(definition.symbol_url, origin).toString()
        : null,
    },
  ]))
}

export async function convertSchematic(
  schematic: SchematicDocument,
  outputFormat: 'cir' | 'internal_json' | 'slicap_sch',
): Promise<{
  netlist_text: string | null
  schematic: SchematicDocument | null
  slicap_schematic: SlicapSchematicDocument | null
  diagnostics: Diagnostic[]
}> {
  return request('/schematics/convert', {
    method: 'POST',
    body: JSON.stringify({ schematic, output_format: outputFormat }),
  })
}

export async function convertNativeSchematic(
  schematic: SlicapSchematicDocument,
  outputFormat: 'cir' | 'internal_json' | 'slicap_sch',
): Promise<{
  netlist_text: string | null
  schematic: SchematicDocument | null
  slicap_schematic: SlicapSchematicDocument | null
  diagnostics: Diagnostic[]
}> {
  return request('/schematics/convert', {
    method: 'POST',
    body: JSON.stringify({ slicap_schematic: schematic, output_format: outputFormat }),
  })
}

export async function importSlicapSchematic(raw: SlicapSchematicDocument): Promise<SchematicDocument> {
  const response = await request<{ schematic: SchematicDocument }>('/schematics/convert', {
    method: 'POST',
    body: JSON.stringify({ slicap_schematic: raw, output_format: 'internal_json' }),
  })
  return response.schematic
}

export async function submitAnalysis(netlist: string, symbolic: boolean): Promise<AnalysisJob> {
  return request('/analyses', {
    method: 'POST',
    body: JSON.stringify({
      netlist_text: netlist,
      modes: symbolic ? ['laplace', 'pz', 'symbolic'] : ['laplace', 'pz'],
      numeric: true,
      magnitude_error_db: 2,
      phase_error_deg: 5,
    }),
  })
}

export function getAnalysis(jobId: string): Promise<AnalysisJob> {
  return request(`/analyses/${jobId}`)
}
