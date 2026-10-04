import { apiClient } from './client';
import type { AuditLogEntry } from '@/types';

export async function fetchAuditLogs() {
  const { data } = await apiClient.get<AuditLogEntry[]>('/audit-logs');
  return data;
}
