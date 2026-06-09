import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ScanProgress } from './ScanProgress';
import type { ScanProgress as ScanProgressType } from '../types';

function makeProgress(over: Partial<ScanProgressType> = {}): ScanProgressType {
  return {
    scan_id: 1,
    status: 'running',
    progress: 0.45,
    message: 'Probing hosts',
    hosts_found: null,
    ...over,
  };
}

describe('ScanProgress', () => {
  it('renders nothing without progress', () => {
    const { container } = render(<ScanProgress progress={null} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('shows the rounded percentage and running label', () => {
    render(<ScanProgress progress={makeProgress({ progress: 0.45 })} />);
    expect(screen.getByText('45%')).toBeInTheDocument();
    expect(screen.getByText('Scanning...')).toBeInTheDocument();
  });

  it('does not show a host count while running (null)', () => {
    render(<ScanProgress progress={makeProgress({ hosts_found: null })} />);
    expect(screen.queryByText(/hosts found/)).not.toBeInTheDocument();
  });

  it('shows the host count once known', () => {
    render(
      <ScanProgress
        progress={makeProgress({ status: 'completed', progress: 1, hosts_found: 7 })}
      />,
    );
    expect(screen.getByText('7 hosts found')).toBeInTheDocument();
    expect(screen.getByText('Scan Complete')).toBeInTheDocument();
  });

  it('renders the failed state', () => {
    render(<ScanProgress progress={makeProgress({ status: 'failed', progress: 0 })} />);
    expect(screen.getByText('Scan Failed')).toBeInTheDocument();
  });
});
