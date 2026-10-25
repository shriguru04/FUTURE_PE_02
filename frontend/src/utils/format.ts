export const parseLines = (text: string): string[] =>
  text.split('\n').map((l) => l.trim()).filter(Boolean)

export const linesToText = (items?: string[]): string => (items ?? []).join('\n')

export const humanize = (s: string): string => s.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())

export const fmtNum = (v: number | null | undefined, digits = 0): string =>
  v === null || v === undefined ? '—' : v.toLocaleString(undefined, { maximumFractionDigits: digits })

export const fmtPct = (v: number | null | undefined): string => (v === null || v === undefined ? '—' : `${v.toFixed(2)}%`)

export const fmtMoney = (v: number | null | undefined): string =>
  v === null || v === undefined ? '—' : v.toLocaleString(undefined, { style: 'currency', currency: 'USD' })

export const fmtDate = (s: string): string => new Date(s).toLocaleString()
