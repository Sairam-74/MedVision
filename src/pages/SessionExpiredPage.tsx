import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

export function SessionExpiredPage() {
  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <Card className="w-full max-w-lg">
        <CardContent className="space-y-4 p-8 text-center">
          <h2 className="text-2xl font-semibold">Your session expired</h2>
          <p className="text-sm text-muted-foreground">Please sign in again to continue working in MedVision AI.</p>
          <Button asChild>
            <Link to="/login">Back to sign in</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
