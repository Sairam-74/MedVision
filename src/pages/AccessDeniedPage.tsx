import { Link } from 'react-router-dom';
import { ShieldAlert } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

export function AccessDeniedPage() {
  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <Card className="w-full max-w-lg">
        <CardContent className="space-y-4 p-8 text-center">
          <ShieldAlert className="mx-auto h-12 w-12 text-primary" aria-hidden="true" />
          <h2 className="text-2xl font-semibold">Access denied</h2>
          <p className="text-sm text-muted-foreground">You do not have permission to open this page with the current role.</p>
          <Button asChild>
            <Link to="/dashboard">Return to dashboard</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
