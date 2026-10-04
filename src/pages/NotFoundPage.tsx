import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <Card className="w-full max-w-lg">
        <CardContent className="space-y-4 p-8 text-center">
          <p className="text-sm uppercase tracking-[0.24em] text-muted-foreground">404</p>
          <h2 className="text-2xl font-semibold">Page not found</h2>
          <p className="text-sm text-muted-foreground">The page you requested does not exist or is unavailable.</p>
          <Button asChild>
            <Link to="/dashboard">Go to dashboard</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
