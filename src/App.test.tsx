import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it } from 'vitest';
import App from './App';
import { fetchAnalysisStatus } from '@/api/analyses';
import { useAuthStore } from '@/store/authStore';
import { mockSession } from '@/mocks/data';

function renderApp(initialPath: string) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialPath]}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

afterEach(() => {
  act(() => {
    useAuthStore.getState().logout();
  });
});

describe('MedVision routing and prediction workflow', () => {
  it('preserves the protected destination after login', async () => {
    const user = userEvent.setup();
    renderApp('/upload');

    expect(await screen.findByRole('heading', { name: /welcome back/i })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /^sign in$/i }));

    expect(await screen.findByRole('heading', { name: /image intake station/i })).toBeInTheDocument();
  });

  it('rejects uploads larger than 10 MB', async () => {
    const user = userEvent.setup();
    act(() => {
      useAuthStore.getState().login(mockSession);
    });
    renderApp('/upload');

    const input = await screen.findByLabelText(/drag and drop an x-ray image here/i);
    const largeFile = new File([new Uint8Array(10 * 1024 * 1024 + 1)], 'large-xray.png', {
      type: 'image/png',
    });

    await user.upload(input, largeFile);

    expect(await screen.findByText(/maximum size is 10 mb/i)).toBeInTheDocument();
  });

  it('supports the prediction polling API contract', async () => {
    await fetchAnalysisStatus('ana-1001');
    await fetchAnalysisStatus('ana-1001');
    const completed = await fetchAnalysisStatus('ana-1001');

    expect(completed.status).toBe('completed');
    expect(completed.progress).toBe(100);
    expect(completed.result?.calibratedThreshold).toBe(0.9);
    expect(completed.result?.severityFeatures?.area).toBeGreaterThan(0);
  });

  it('renders real prediction fields on the result desk', async () => {
    act(() => {
      useAuthStore.getState().login(mockSession);
    });
    renderApp('/results/ana-1001');

    expect(await screen.findByRole('heading', { name: /prediction result/i })).toBeInTheDocument();
    expect(screen.getByText('Before')).toBeInTheDocument();
    expect(screen.getByText('After')).toBeInTheDocument();
    expect(screen.queryByText(/threshold/i)).not.toBeInTheDocument();
    expect(screen.queryByText('0.4526')).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /download report/i })).not.toBeInTheDocument();
  });
});
