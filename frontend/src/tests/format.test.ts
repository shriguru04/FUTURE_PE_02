import { describe, expect, it } from 'vitest'
import { fmtMoney, fmtNum, fmtPct, humanize, linesToText, parseLines } from '../utils/format'

describe('format helpers', () => {
  it('parses one-item-per-line text, dropping blanks', () => {
    expect(parseLines(' a \n\n b\n   \nc')).toEqual(['a', 'b', 'c'])
    expect(linesToText(['a', 'b'])).toBe('a\nb')
    expect(linesToText(undefined)).toBe('')
  })
  it('shows missing metrics as a dash, never zero', () => {
    expect(fmtNum(null)).toBe('—')
    expect(fmtPct(undefined)).toBe('—')
    expect(fmtMoney(null)).toBe('—')
    expect(fmtPct(5)).toBe('5.00%')
    expect(fmtNum(0)).toBe('0')
  })
  it('humanizes snake_case', () => expect(humanize('ready_for_review')).toBe('Ready For Review'))
})
