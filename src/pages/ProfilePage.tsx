import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PageHeader } from '@/components/layout/PageHeader';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';

export function ProfilePage() {
  return (
    <div className="space-y-6">
      <PageHeader title="Profile / Settings" description="Manage personal details, password, notifications, active sessions, and MFA enrollment." />
      <Tabs defaultValue="account" className="space-y-4">
        <TabsList>
          <TabsTrigger value="account">My Account</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
        </TabsList>
        <TabsContent value="account">
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader><CardTitle>Personal info</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2"><Label htmlFor="fullName">Full name</Label><Input id="fullName" defaultValue="Demo Clinician" /></div>
                <div className="space-y-2"><Label htmlFor="email">Email</Label><Input id="email" defaultValue="demo.clinician@example.invalid" /></div>
                <div className="space-y-2"><Label htmlFor="orgRole">Organization role</Label><Input id="orgRole" defaultValue="Clinician" /></div>
                <Button>Save changes</Button>
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Notifications</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                {['New result available', 'Approval request assigned', 'Security events'].map((label) => (
                  <div key={label} className="flex items-center justify-between rounded-lg border border-border px-4 py-3">
                    <span className="text-sm font-medium">{label}</span>
                    <Switch defaultChecked />
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        <TabsContent value="security">
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader><CardTitle>Change password</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2"><Label htmlFor="current">Current password</Label><Input id="current" type="password" /></div>
                <div className="space-y-2"><Label htmlFor="new">New password</Label><Input id="new" type="password" /></div>
                <div className="space-y-2"><Label htmlFor="confirm">Confirm password</Label><Input id="confirm" type="password" /></div>
                <Button>Update password</Button>
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Active sessions</CardTitle></CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div className="rounded-lg border border-border p-4"><div className="flex items-center justify-between"><span>Windows workstation</span><Badge variant="secondary">Current</Badge></div><p className="mt-1 text-muted-foreground">Boston, MA · Edge</p></div>
                <div className="rounded-lg border border-border p-4"><div className="flex items-center justify-between"><span>Tablet session</span><Button variant="outline" size="sm">Revoke</Button></div><p className="mt-1 text-muted-foreground">Cambridge, MA · Safari</p></div>
                <div className="rounded-lg border border-border p-4"><p className="font-medium">MFA enrollment</p><p className="mt-1 text-muted-foreground">One-time passcode support can be enabled from the backend policy.</p></div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
