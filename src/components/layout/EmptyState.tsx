import { ReactNode } from 'react';
import { Card } from '@/components/ui/card';

export function EmptyState({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return (
    <Card className="border-dashed bg-muted/30">
      <div className="flex flex-col items-start gap-4 p-8">
        <div>
          <h3 className="text-lg font-semibold">{title}</h3>
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">{description}</p>
        </div>
        {action}
      </div>
    </Card>
  );
}
