import { apiClient } from './client';
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

export async function refreshSession() {
  const { data } = await apiClient.post<AuthSession>('/auth/refresh');
  return data;
}

export async function signup(request: SignupRequest) {
  const { data } = await apiClient.post<{ message: string }>('/auth/signup', request);
  return data;
}

export async function sendPasswordReset(request: PasswordResetRequest) {
  const { data } = await apiClient.post<{ message: string }>('/auth/forgot-password', request);
  return data;
}

export async function resetPassword(request: ResetPasswordRequest) {
  const { data } = await apiClient.post<{ message: string }>('/auth/reset-password', request);
  return data;
}
