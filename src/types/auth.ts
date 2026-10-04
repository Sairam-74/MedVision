export type UserRole = 'technician' | 'clinician' | 'admin';

export interface AuthSession {
  user: AppUser;
  accessToken: string;
  expiresAt: string;
}

export interface AppUser {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  status: 'active' | 'pending' | 'suspended';
  organization: string;
}

export interface LoginRequest {
  identifier: string;
  password: string;
  otp?: string;
}

export interface SignupRequest {
  name: string;
  email: string;
  password: string;
}

export interface PasswordResetRequest {
  email: string;
}

export interface ResetPasswordRequest {
  token: string;
  password: string;
}
