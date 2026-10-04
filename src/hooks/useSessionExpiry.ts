import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';

export function useSessionExpiry() {
  const markSessionExpired = useAuthStore((state) => state.markSessionExpired);
  const navigate = useNavigate();

  useEffect(() => {
    const handler = () => {
      markSessionExpired();
      navigate('/session-expired', { replace: true });
    };
    window.addEventListener('medvision:session-expired', handler as EventListener);
    return () => window.removeEventListener('medvision:session-expired', handler as EventListener);
  }, [markSessionExpired, navigate]);
}
