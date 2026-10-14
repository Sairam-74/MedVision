import { fireEvent, render, screen } from '@testing-library/react';
import { beforeAll, describe, expect, it, vi } from 'vitest';
import { XrayViewer } from './XrayViewer';
import { clampPan } from './viewerGeometry';
import type { PredictionResult } from '@/types';
beforeAll(() =>
  vi.stubGlobal(
    'ResizeObserver',
    class {
      observe() {}
      disconnect() {}
    },
  ),
);
const result: PredictionResult = {
  id: 'fixture',
  analysisId: 'synthetic',
  fractureStatus: 'needs_review',
  severity: 'not_applicable',
  region: 'Unsupported',
  type: 'Segmentation',
  recommendation: 'Review',
  imageUrl: '/synthetic.png',
  maskPngBase64: 'synthetic-test-mask',
  maskShape: [80, 64],
  disclaimer: 'Research fixture',
};
describe('shared viewer geometry', () => {
  it('bounds panning so zoomed images cannot disappear', () => {
    expect(clampPan(5000, -5000, 2, 600, 450)).toEqual({ x: 300, y: -225 });
    expect(clampPan(50, 50, 1, 600, 450)).toEqual({ x: 0, y: 0 });
  });
  it('changes display filters and numeric outputs, resetting without changing inference data', () => {
    render(<XrayViewer result={result} />);
    const original = screen.getByAltText('Original X-ray');
    fireEvent.change(screen.getByLabelText('Brightness'), {
      target: { value: '140' },
    });
    fireEvent.change(screen.getByLabelText('Contrast'), {
      target: { value: '130' },
    });
    expect(original).toHaveStyle({ filter: 'brightness(140%) contrast(130%)' });
    expect(screen.getByText('140%')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Reset all adjustments'));
    expect(original).toHaveStyle({ filter: 'brightness(100%) contrast(100%)' });
    expect(result.imageUrl).toBe('/synthetic.png');
  });
  it('applies zoom to the shared layer transform and honors limits', () => {
    render(<XrayViewer result={result} />);
    fireEvent.click(screen.getByText('Zoom in'));
    expect(screen.getByTestId('viewer-transform').style.transform).toContain(
      'scale(1.25)',
    );
    for (let i = 0; i < 50; i++) fireEvent.click(screen.getByText('Zoom in'));
    expect(screen.getByLabelText('Zoom level')).toHaveTextContent('800%');
    fireEvent.wheel(screen.getByTestId('viewer-viewport'), { deltaY: 100 });
    expect(
      screen.getByTestId('viewer-transform').style.transform,
    ).not.toContain('scale(8)');
    fireEvent.click(screen.getByText('Fit to screen / Reset zoom'));
    expect(screen.getByLabelText('Zoom level')).toHaveTextContent('100%');
  });
  it('hides an incorrectly sized overlay instead of mislocalizing it', () => {
    render(<XrayViewer result={result} />);
    const original = screen.getByAltText('Original X-ray');
    Object.defineProperty(original, 'naturalWidth', { value: 100 });
    Object.defineProperty(original, 'naturalHeight', { value: 100 });
    fireEvent.load(original);
    expect(screen.getByRole('alert')).toHaveTextContent(
      'Mask dimensions do not match',
    );
    expect(
      screen.queryByLabelText('Aligned segmentation overlay'),
    ).not.toBeInTheDocument();
  });
});
