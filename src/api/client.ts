import axios, { AxiosError } from 'axios';
import { clearAccessToken, getAccessToken } from './authTokenService';

const baseURL = import.meta.env.VITE_API_BASE_URL || '/';

export const apiClient = axios.create({
  baseURL,
  withCredentials: true,
  timeout: 15000,
});

apiClient.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ message?: string }>) => {
    if (error.response?.status === 401 && !['/auth/login', '/auth/refresh'].includes(error.config?.url ?? '')) {
      clearAccessToken();
      window.dispatchEvent(new CustomEvent('medvision:session-expired'));
    }
    return Promise.reject(error);
  },
);

export function imageUrl(url?: string) {
  if (!url || !url.startsWith('/generated/')) return url;
  return new URL(url, new URL(baseURL, window.location.origin)).href;
}
