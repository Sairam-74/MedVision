import type { UserRole } from './auth';

export type AuditAction = 'uploaded' | 'viewed' | 'approved' | 'flagged' | 'noted' | 'signed_in' | 'signed_out';

export interface AuditLogEntry {
  id: string;
  userName: string;
  userRole: UserRole;
  action: AuditAction;
  analysisId?: string;
  createdAt: string;
  details?: string;
}
