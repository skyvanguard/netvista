import { describe, it, expect } from 'vitest';
import { riskColor, riskLabel, formatDuration } from '../formatters';

describe('riskColor', () => {
  it('returns red for critical risk', () => {
    expect(riskColor(8)).toBe('#ef4444');
  });
  it('returns amber for high risk', () => {
    expect(riskColor(5)).toBe('#f59e0b');
  });
  it('returns yellow for medium risk', () => {
    expect(riskColor(2)).toBe('#eab308');
  });
  it('returns green for low risk', () => {
    expect(riskColor(0)).toBe('#22c55e');
  });
});

describe('riskLabel', () => {
  it('returns Critical for >= 7', () => {
    expect(riskLabel(7)).toBe('Critical');
  });
  it('returns Low for 0', () => {
    expect(riskLabel(0)).toBe('Low');
  });
});

describe('formatDuration', () => {
  it('returns dash for null input', () => {
    expect(formatDuration(null, null)).toBe('\u2014');
  });
  it('formats seconds', () => {
    const start = '2024-01-01T00:00:00Z';
    const end = '2024-01-01T00:00:30Z';
    expect(formatDuration(start, end)).toBe('30s');
  });
  it('formats minutes and seconds', () => {
    const start = '2024-01-01T00:00:00Z';
    const end = '2024-01-01T00:02:15Z';
    expect(formatDuration(start, end)).toBe('2m 15s');
  });
});
