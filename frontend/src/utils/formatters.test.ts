import { describe, it, expect } from 'vitest';
import { riskColor, riskLabel, formatDate, formatDuration } from './formatters';

describe('riskLabel', () => {
  it('maps score ranges to labels', () => {
    expect(riskLabel(8)).toBe('Critical');
    expect(riskLabel(7)).toBe('Critical');
    expect(riskLabel(5)).toBe('High');
    expect(riskLabel(2)).toBe('Medium');
    expect(riskLabel(0)).toBe('Low');
  });
});

describe('riskColor', () => {
  it('returns a distinct color per severity band', () => {
    const colors = new Set([riskColor(9), riskColor(5), riskColor(2), riskColor(0)]);
    expect(colors.size).toBe(4);
  });
});

describe('formatDate', () => {
  it('returns a dash for null', () => {
    expect(formatDate(null)).toBe('—');
  });
  it('formats a real ISO date to a non-empty string', () => {
    expect(formatDate('2026-06-09T12:00:00Z')).not.toBe('—');
  });
});

describe('formatDuration', () => {
  it('returns a dash when either bound is missing', () => {
    expect(formatDuration(null, '2026-06-09T12:00:10Z')).toBe('—');
    expect(formatDuration('2026-06-09T12:00:00Z', null)).toBe('—');
  });
  it('formats sub-minute durations in seconds', () => {
    expect(formatDuration('2026-06-09T12:00:00Z', '2026-06-09T12:00:45Z')).toBe('45s');
  });
  it('formats longer durations as minutes and seconds', () => {
    expect(formatDuration('2026-06-09T12:00:00Z', '2026-06-09T12:02:05Z')).toBe('2m 5s');
  });
});
