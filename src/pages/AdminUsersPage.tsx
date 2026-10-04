import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchUsers } from '@/api/users';
import { PageHeader } from '@/components/layout/PageHeader';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

export function AdminUsersPage() {
  const { data: users = [] } = useQuery({ queryKey: ['users'], queryFn: fetchUsers });
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('technician');

  return (
    <div className="space-y-6">
      <PageHeader
        title="User management"
        description="Admin-only view for listing users, changing role assignments, and sending new invitations."
        actions={
          <Dialog>
            <DialogTrigger asChild>
              <Button>Invite user</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Invite user</DialogTitle>
                <DialogDescription>Send an invitation to a new staff member.</DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="space-y-2"><Label htmlFor="inviteEmail">Email</Label><Input id="inviteEmail" value={inviteEmail} onChange={(event) => setInviteEmail(event.target.value)} /></div>
                <div className="space-y-2"><Label htmlFor="inviteRole">Role</Label><Input id="inviteRole" value={inviteRole} onChange={(event) => setInviteRole(event.target.value)} /></div>
                <div className="flex justify-end gap-3"><Button variant="outline">Cancel</Button><Button>Send invite</Button></div>
              </div>
            </DialogContent>
          </Dialog>
        }
      />
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Status</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.map((user) => (
                <TableRow key={user.id}>
                  <TableCell className="font-medium">{user.name}</TableCell>
                  <TableCell>{user.email}</TableCell>
                  <TableCell><Badge variant="outline" className="capitalize">{user.role}</Badge></TableCell>
                  <TableCell><Badge variant={user.status === 'active' ? 'success' : user.status === 'pending' ? 'warning' : 'destructive'} className="capitalize">{user.status}</Badge></TableCell>
                  <TableCell className="text-right"><Button variant="outline" size="sm">Deactivate</Button></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
