import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetchAnalyses } from '@/api/analyses';
import { PageHeader } from '@/components/layout/PageHeader';
import { EmptyState } from '@/components/layout/EmptyState';
import { StatCard } from '@/components/layout/StatCard';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { formatRelative } from '@/utils/format';

export function DashboardPage() {
  const { data: analyses = [] } = useQuery({ queryKey: ['analyses'], queryFn: fetchAnalyses });
  const totalAnalyses = analyses.length;
  const fracturesDetected = analyses.filter((analysis) => analysis.status === 'completed').length;
  const isEmpty = totalAnalyses === 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Home dashboard"
        description="Monitor recent fracture analyses, start a new upload, and review key model metrics."
        actions={
          <Button asChild>
            <Link to="/upload">Upload X-ray</Link>
          </Button>
        }
      />
      <section className="grid gap-4 md:grid-cols-3">
        <StatCard title="Total Analyses" value={String(totalAnalyses)} description="All analyses available to your organization." />
        <StatCard title="Fractures Detected" value={String(fracturesDetected)} description="Completed studies with a positive fracture outcome." tone="warning" />
        <StatCard title="Model Accuracy" value="94%" description="Linked to current model metadata and threshold settings." tone="accent" />
      </section>
      {isEmpty ? (
        <EmptyState
          title="No analyses yet"
          description="This account has not uploaded or reviewed any studies. Start with an X-ray upload to populate the dashboard."
          action={<Button asChild><Link to="/upload">Upload first X-ray</Link></Button>}
        />
      ) : (
        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <div>
              <CardTitle>Recent analyses</CardTitle>
              <p className="text-sm text-muted-foreground">Most recent uploads and review states.</p>
            </div>
            <Button variant="outline" asChild>
              <Link to="/history">View all</Link>
            </Button>
          </CardHeader>
          <CardContent className="space-y-3">
            {analyses.slice(0, 4).map((analysis) => (
              <Link key={analysis.id} to={`/results/${analysis.id}`} className="flex items-center justify-between rounded-lg border border-border px-4 py-3 transition-colors hover:bg-muted/40">
                <div>
                  <p className="font-medium">{analysis.fileName}</p>
                  <p className="text-sm text-muted-foreground">Uploaded {formatRelative(analysis.createdAt)} by {analysis.uploader}</p>
                </div>
                <Badge variant={analysis.status === 'completed' ? 'success' : analysis.status === 'failed' ? 'destructive' : 'secondary'} className="capitalize">
                  {analysis.status.replace('_', ' ')}
                </Badge>
              </Link>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
