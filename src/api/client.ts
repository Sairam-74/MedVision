import axios, { AxiosError } from 'axios';
import { clearAccessToken, getAccessToken } from './authTokenService';

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api';

export const apiClient = axios.create({
  baseURL,
  withCredentials: true,
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
    if (error.response?.status === 401 && error.config?.url !== '/auth/login') {
      clearAccessToken();
      window.dispatchEvent(new CustomEvent('medvision:session-expired'));
    }
    return Promise.reject(error);
  },
);
