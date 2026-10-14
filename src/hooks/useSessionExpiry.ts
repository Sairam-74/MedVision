import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { useQueryClient } from '@tanstack/react-query';
import { useMockMode } from '@/utils/env';

export function useSessionExpiry() {
  const markSessionExpired = useAuthStore((state) => state.markSessionExpired);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const expiresAt = useAuthStore((state) => state.expiresAt);
  const mockMode = useMockMode();

  useEffect(() => {
    const handler = () => {
      markSessionExpired();
      queryClient.clear();
      navigate('/session-expired', { replace: true });
    };
    window.addEventListener('medvision:session-expired', handler as EventListener);
    const deadline = expiresAt ? Date.parse(expiresAt) : NaN;
    const timer = !mockMode && Number.isFinite(deadline) ? window.setTimeout(handler, Math.max(0, deadline - Date.now())) : undefined;
    return () => {
      window.removeEventListener('medvision:session-expired', handler as EventListener);
      if (timer !== undefined) window.clearTimeout(timer);
    };
  }, [markSessionExpired, navigate, queryClient, expiresAt, mockMode]);
}
