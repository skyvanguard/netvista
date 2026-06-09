import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { SearchBar } from './SearchBar';

describe('SearchBar', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it('debounces onSearch until the user pauses typing', () => {
    const onSearch = vi.fn();
    render(<SearchBar onSearch={onSearch} />);
    const input = screen.getByPlaceholderText(/search/i);

    // The mount effect fires once with the empty initial value.
    act(() => vi.advanceTimersByTime(200));
    onSearch.mockClear();

    fireEvent.change(input, { target: { value: '19' } });
    fireEvent.change(input, { target: { value: '192' } });

    // Nothing yet — still within the debounce window.
    expect(onSearch).not.toHaveBeenCalled();

    act(() => vi.advanceTimersByTime(200));

    // Only the final value is sent, once.
    expect(onSearch).toHaveBeenCalledTimes(1);
    expect(onSearch).toHaveBeenCalledWith('192');
  });
});
