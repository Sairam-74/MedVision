import { create } from 'zustand';
import type { AppUser, AuthSession, UserRole } from '@/types';
import { clearAccessToken, setAccessToken } from '@/api/authTokenService';

interface AuthState {
  user: AppUser | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  expiresAt: string | null;
  login: (session: AuthSession) => void;
  logout: () => void;
  markSessionExpired: () => void;
  hasRole: (roles: UserRole[]) => boolean;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  isAuthenticated: false,
  expiresAt: null,
  login: (session) => {
    setAccessToken(session.accessToken);
    set({ user: session.user, accessToken: session.accessToken, expiresAt: session.expiresAt ?? null, isAuthenticated: true });
  },
  logout: () => {
    clearAccessToken();
    set({ user: null, accessToken: null, expiresAt: null, isAuthenticated: false });
  },
  markSessionExpired: () => {
    clearAccessToken();
    set({ user: null, accessToken: null, expiresAt: null, isAuthenticated: false });
  },
  hasRole: (roles) => {
    const user = get().user;
    return Boolean(user && roles.includes(user.role));
  },
}));
