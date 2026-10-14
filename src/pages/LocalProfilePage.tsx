import { useAuthStore } from '@/store/authStore';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PageHeader } from '@/components/layout/PageHeader';

export function LocalProfilePage() {
  const user = useAuthStore((state) => state.user);
  return (
    <div className="space-y-6">
      <PageHeader title="Profile" description="Your local research account." />
      <Card>
        <CardHeader><CardTitle>Account details</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <p><strong>Name:</strong> {user?.name}</p>
          <p><strong>Email:</strong> {user?.email}</p>
          <p><strong>Organization:</strong> {user?.organization}</p>
          <p><strong>Role:</strong> {user?.role}</p>
          <p className="text-sm text-muted-foreground">Account editing, password recovery and MFA enrollment are unavailable in this local demo. Sign out using Logout.</p>
        </CardContent>
      </Card>
    </div>
  );
}
