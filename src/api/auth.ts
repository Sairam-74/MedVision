import { apiClient } from './client';
import { isAxiosError } from 'axios';
import type {
  AuthSession,
  LoginRequest,
  PasswordResetRequest,
  ResetPasswordRequest,
  SignupRequest,
} from '@/types';

export async function login(request: LoginRequest) {
  const { data } = await apiClient.post<AuthSession>('/auth/login', request);
  return data;
}

let refreshing: Promise<AuthSession> | null = null;
export function refreshSession() {
  refreshing ??= apiClient.post<AuthSession>('/auth/refresh')
    .then(({ data }) => data).finally(() => { refreshing = null; });
  return refreshing;
}

export async function logoutSession() {
  await apiClient.post('/auth/logout');
}

export async function signup(request: SignupRequest) {
  const { data } = await apiClient.post<{ message: string; recoveryCode: string }>('/auth/signup', request);
  return data;
}

export async function sendPasswordReset(request: PasswordResetRequest) {
  const { data } = await apiClient.post<{ message: string; resetUrl: string }>('/auth/forgot-password', request);
  return data;
}

export async function resetPassword(request: ResetPasswordRequest) {
  const { data } = await apiClient.post<{ message: string; recoveryCode: string }>('/auth/reset-password', request);
  return data;
}

export async function fetchDemoCredentials() {
  return (await apiClient.get<{ enabled: boolean; email?: string; password?: string }>('/auth/demo-credentials')).data;
}

export function authErrorMessage(error: unknown, fallback: string) {
  if (!isAxiosError(error)) return fallback;
  if (!error.response) return 'Cannot reach the local service. Check that the demo is running and try again.';
  if (error.response.status === 429) return 'Too many attempts. Wait a minute before trying again.';
  const detail = error.response.data?.detail;
  return typeof detail === 'string' ? detail : fallback;
}
