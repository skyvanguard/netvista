import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useScanProgress } from './useScanProgress';

// Minimal WebSocket stand-in that records instances and lets tests drive
// onmessage/onclose manually.
class MockWebSocket {
  static instances: MockWebSocket[] = [];
  url: string;
  onmessage: ((e: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  close = vi.fn();

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }

  emit(payload: object) {
    this.onmessage?.({ data: JSON.stringify(payload) });
  }
}

const last = () => MockWebSocket.instances[MockWebSocket.instances.length - 1];

beforeEach(() => {
  MockWebSocket.instances = [];
  vi.stubGlobal('WebSocket', MockWebSocket as unknown as typeof WebSocket);
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe('useScanProgress', () => {
  it('connects once when given a scanId', () => {
    renderHook(() => useScanProgress(1));
    expect(MockWebSocket.instances).toHaveLength(1);
  });

  it('does not connect when scanId is null', () => {
    renderHook(() => useScanProgress(null));
    expect(MockWebSocket.instances).toHaveLength(0);
  });

  it('exposes the latest progress message', () => {
    const { result } = renderHook(() => useScanProgress(1));
    act(() => last().emit({ scan_id: 1, status: 'running', progress: 0.5, message: 'half' }));
    expect(result.current?.progress).toBe(0.5);
  });

  it('reconnects with backoff after an unexpected close', () => {
    renderHook(() => useScanProgress(1));
    expect(MockWebSocket.instances).toHaveLength(1);

    act(() => last().onclose?.());
    // Still within the backoff window — no reconnect yet.
    expect(MockWebSocket.instances).toHaveLength(1);

    act(() => vi.advanceTimersByTime(1000));
    expect(MockWebSocket.instances).toHaveLength(2);
  });

  it('stops reconnecting once the scan reaches a terminal state', () => {
    renderHook(() => useScanProgress(1));
    act(() => last().emit({ scan_id: 1, status: 'completed', progress: 1, message: 'done' }));
    act(() => last().onclose?.());
    act(() => vi.advanceTimersByTime(10_000));
    expect(MockWebSocket.instances).toHaveLength(1); // no reconnect
  });

  it('closes the socket on unmount', () => {
    const { unmount } = renderHook(() => useScanProgress(1));
    const ws = last();
    unmount();
    expect(ws.close).toHaveBeenCalled();
  });
});
