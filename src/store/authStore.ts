import { create } from 'zustand';
import type { AppUser, AuthSession, UserRole } from '@/types';
import { clearAccessToken, setAccessToken } from '@/api/authTokenService';

interface AuthState {
  user: AppUser | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  login: (session: AuthSession) => void;
  logout: () => void;
  markSessionExpired: () => void;
  hasRole: (roles: UserRole[]) => boolean;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  isAuthenticated: false,
  login: (session) => {
    setAccessToken(session.accessToken);
    set({ user: session.user, accessToken: session.accessToken, isAuthenticated: true });
  },
  logout: () => {
    clearAccessToken();
    set({ user: null, accessToken: null, isAuthenticated: false });
  },
  markSessionExpired: () => {
    clearAccessToken();
    set({ user: null, accessToken: null, isAuthenticated: false });
  },
  hasRole: (roles) => {
    const user = get().user;
    return Boolean(user && roles.includes(user.role));
  },
}));
