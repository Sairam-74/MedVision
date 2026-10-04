import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/utils/cn';

export function StatCard({ title, value, description, tone = 'default' }: { title: string; value: string; description?: string; tone?: 'default' | 'accent' | 'warning' }) {
  return (
    <Card className={cn('overflow-hidden', tone === 'accent' && 'border-primary/30 bg-primary/5', tone === 'warning' && 'border-amber-300 bg-amber-50')}>
      <CardHeader className="space-y-2">
        <CardDescription>{title}</CardDescription>
        <CardTitle className="text-3xl">{value}</CardTitle>
      </CardHeader>
      {description ? <CardContent className="pt-0 text-sm text-muted-foreground">{description}</CardContent> : null}
    </Card>
  );
}
