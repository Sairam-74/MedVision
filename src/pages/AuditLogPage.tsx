import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchAuditLogs } from '@/api/audit';
import { PageHeader } from '@/components/layout/PageHeader';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { formatDateTime } from '@/utils/format';

export function AuditLogPage() {
  const { data: logs = [] } = useQuery({ queryKey: ['audit-logs'], queryFn: fetchAuditLogs });
  const [userFilter, setUserFilter] = useState('');
  const [dateFilter, setDateFilter] = useState('');

  const filtered = useMemo(() => {
    return logs.filter((entry) => {
      const matchesUser = entry.userName.toLowerCase().includes(userFilter.toLowerCase());
      const matchesDate = dateFilter ? entry.createdAt.startsWith(dateFilter) : true;
      return matchesUser && matchesDate;
    });
  }, [dateFilter, logs, userFilter]);

  return (
    <div className="space-y-6">
      <PageHeader title="Audit log" description="Read-only activity trail for uploads, views, approvals, and security actions." />
      <Card>
        <CardContent className="grid gap-3 p-4 md:grid-cols-2">
          <Input placeholder="Filter by user" value={userFilter} onChange={(event) => setUserFilter(event.target.value)} />
          <Input type="date" value={dateFilter} onChange={(event) => setDateFilter(event.target.value)} />
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>User</TableHead>
                <TableHead>Action</TableHead>
                <TableHead>Analysis</TableHead>
                <TableHead>When</TableHead>
                <TableHead>Details</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((entry) => (
                <TableRow key={entry.id}>
                  <TableCell>
                    <div>
                      <p className="font-medium">{entry.userName}</p>
                      <Badge variant="outline" className="mt-1 capitalize">{entry.userRole}</Badge>
                    </div>
                  </TableCell>
                  <TableCell className="capitalize">{entry.action}</TableCell>
                  <TableCell>{entry.analysisId || 'Global'}</TableCell>
                  <TableCell>{formatDateTime(entry.createdAt)}</TableCell>
                  <TableCell>{entry.details || '—'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
