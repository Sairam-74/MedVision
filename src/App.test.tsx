import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it } from 'vitest';
import App from './App';
import { fetchAnalysisStatus } from '@/api/analyses';
import { useAuthStore } from '@/store/authStore';
import { mockSession } from '@/mocks/data';

function renderApp(initialPath: string, existingClient?: QueryClient) {
  const queryClient = existingClient ?? new QueryClient({
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
  it('creates an account and automatically redirects to login with its recovery receipt', async () => {
    const user = userEvent.setup();
    renderApp('/signup');
    await user.type(await screen.findByLabelText('Full name'), 'Research User');
    await user.type(screen.getByLabelText('Email'), 'research@example.invalid');
    await user.type(screen.getByLabelText('Password', { exact: true }), 'long-unique-passphrase');
    await user.type(screen.getByLabelText('Confirm password'), 'long-unique-passphrase');
    await user.click(screen.getByRole('button', { name: /^sign up$/i }));
    expect(await screen.findByRole('heading', { name: 'Welcome back' })).toBeInTheDocument();
    expect(screen.getByLabelText('Recovery code')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Continue to sign in' })).not.toBeInTheDocument();
    expect(await screen.findByLabelText('Email')).toHaveValue('research@example.invalid');
    expect(screen.getByLabelText('Password', { exact: true })).toHaveValue('');
  });

  it('requires a valid link before presenting the password reset form', async () => {
    renderApp('/reset-password');
    expect(await screen.findByRole('heading', { name: 'Reset link required' })).toBeInTheDocument();
    expect(screen.queryByLabelText('New password')).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Start account recovery' })).toBeInTheDocument();
  });
  it('preserves the protected destination after login', async () => {
    const user = userEvent.setup();
    renderApp('/upload');

    expect(await screen.findByRole('heading', { name: /welcome back/i })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /^sign in$/i }));

    expect(await screen.findByRole('heading', { name: /patient and study intake/i })).toBeInTheDocument();
  });

  it('collects patient and examination data before enabling image submission', async () => {
    act(() => useAuthStore.getState().login(mockSession));
    renderApp('/upload');
    expect(await screen.findByLabelText('Patient name')).toBeInTheDocument();
    expect(screen.getByLabelText('Examination date')).toBeRequired();
    expect(screen.queryByLabelText('Study X-ray')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name:'Save study and upload views' })).toBeInTheDocument();
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
    expect(screen.getByLabelText('Display layer')).toBeInTheDocument();
    expect(screen.getByAltText('Original X-ray')).toBeInTheDocument();
    expect(screen.getByText('Decision threshold')).toBeInTheDocument();
    expect(screen.getByText('0.90')).toBeInTheDocument();
    expect(screen.queryByText('0.4526')).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /download report/i })).not.toBeInTheDocument();
  });

  it('shows an empty mask without declaring the image healthy', async () => {
    act(() => useAuthStore.getState().login(mockSession));
    renderApp('/results/ana-1003');
    expect(await screen.findByText('No predicted region')).toBeInTheDocument();
    expect(screen.queryByText('no fracture')).not.toBeInTheDocument();
  });

  it('distinguishes an uncertain result', async () => {
    act(() => useAuthStore.getState().login(mockSession));
    renderApp('/results/ana-1002');
    expect(await screen.findByText('Needs review')).toBeInTheDocument();
  });

  it('clears a previous account\'s cached results when signing in again', async () => {
    const user = userEvent.setup();
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    client.setQueryData(['analysis', 'previous-private-case'], { imageUrl: 'private-image' });
    act(() => useAuthStore.getState().login({ ...mockSession, user: { ...mockSession.user, id: 'previous-user' } }));
    renderApp('/login', client);
    const email = await screen.findByLabelText('Email', { exact: true });
    await user.clear(email);
    await user.type(email, 'demo.clinician@example.invalid');
    const password = screen.getByLabelText('Password', { exact: true });
    await user.clear(password);
    await user.type(password, 'password123');
    await user.click(await screen.findByRole('button', { name: /^sign in$/i }));
    expect(useAuthStore.getState().user?.id).toBe(mockSession.user.id);
    expect(client.getQueryData(['analysis', 'previous-private-case'])).toBeUndefined();
    expect(await screen.findByRole('heading', { name: /home dashboard/i }, { timeout: 5000 })).toBeInTheDocument();
  }, 10000);
});
