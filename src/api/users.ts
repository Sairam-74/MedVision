import { apiClient } from './client';
import type { AppUser } from '@/types';

export async function fetchUsers() {
  const { data } = await apiClient.get<AppUser[]>('/users');
  return data;
}
