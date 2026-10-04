import { useMemo } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Activity, Download, FileClock, ScanLine } from 'lucide-react';
import { fetchAnalysisById } from '@/api/analyses';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PageHeader } from '@/components/layout/PageHeader';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { formatPercent } from '@/utils/format';

export function ResultsPage() {
  const { analysisId = '' } = useParams();
  const { data, isLoading } = useQuery({ queryKey: ['analysis', analysisId], queryFn: () => fetchAnalysisById(analysisId), enabled: Boolean(analysisId) });
  const canApprove = true;
  const logAction = useMutation({ mutationFn: async (action: string) => ({ action }) });
  const statusColor = useMemo(() => {
    if (!data) return 'secondary';
    return data.fractureStatus === 'fracture' ? 'destructive' : data.fractureStatus === 'no_fracture' ? 'success' : 'warning';
  }, [data]);
  const originalImage = data?.originalImageUrl ?? data?.imageUrl;
  const overlayImage = data?.overlayUrl ?? (data?.maskPngBase64 ? `data:image/png;base64,${data.maskPngBase64}` : data?.imageUrl);

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading result…</p>;
  }

  if (!data) {
    return <p className="text-sm text-muted-foreground">Result not found.</p>;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Prediction result"
        description="Review the model output, compare the original and overlay views, and capture clinician approval where required."
        actions={
          <>
            <Button variant="outline" asChild>
              <Link to="/upload">New analysis</Link>
            </Button>
            {data.reportUrl ? (
              <Button asChild>
                <a href={data.reportUrl} aria-label="Download report as PDF">
                  <Download className="h-4 w-4" /> Download report
                </a>
              </Button>
            ) : null}
          </>
        }
      />
      <Alert>
        <AlertTitle>AI-assisted result</AlertTitle>
        <AlertDescription>{data.disclaimer}</AlertDescription>
      </Alert>
      <div className="grid gap-6 lg:grid-cols-[1.4fr_0.9fr]">
        <Card className="overflow-hidden border-slate-200 shadow-soft">
          <CardHeader className="border-b border-border bg-slate-950 text-slate-50">
            <div className="flex items-center justify-between gap-3">
              <CardTitle className="flex items-center gap-2">
                <ScanLine className="h-5 w-5 text-cyan-300" /> Evidence viewer
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent className="bg-slate-100 p-4">
            <div className="grid gap-4 md:grid-cols-2">
            <figure className="overflow-hidden rounded-lg border border-slate-300 bg-black">
              <figcaption className="border-b border-slate-700 bg-slate-950 px-4 py-2 text-center text-sm font-semibold uppercase tracking-[0.18em] text-slate-100">Before</figcaption>
              <img src={originalImage} alt="Original X-ray study" className="aspect-square w-full object-cover" />
            </figure>
            <figure className="overflow-hidden rounded-lg border border-slate-300 bg-black">
              <figcaption className="border-b border-slate-700 bg-slate-950 px-4 py-2 text-center text-sm font-semibold uppercase tracking-[0.18em] text-cyan-100">After</figcaption>
              <img src={overlayImage} alt="Prediction overlay highlighting suspected fracture region" className="aspect-square w-full object-cover" />
            </figure>
            </div>
          </CardContent>
        </Card>
        <Card className="border-slate-200 shadow-soft">
          <CardHeader>
            <div className="flex items-start justify-between gap-3">
              <div>
                <CardTitle className="flex items-center gap-2"><Activity className="h-5 w-5" /> Result summary</CardTitle>
                <p className="text-sm text-muted-foreground">Case {data.analysisId}</p>
              </div>
              <Badge variant={statusColor as never} className="capitalize">{data.fractureStatus.replace('_', ' ')}</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm text-muted-foreground">Confidence</p>
              <p className="text-3xl font-semibold">{formatPercent(data.confidence)}</p>
            </div>
            <div className="grid gap-3 text-sm">
              <div>
                <p className="text-muted-foreground">Severity</p>
                <p className="font-medium capitalize">{data.severity}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Region</p>
                <p className="font-medium">{data.region}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Type</p>
                <p className="font-medium">{data.type}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Recommendation</p>
                <p className="font-medium">{data.recommendation}</p>
              </div>
            </div>
            {canApprove ? (
              <div className="space-y-2 rounded-xl border border-border bg-muted/20 p-4">
                <p className="flex items-center gap-2 text-sm font-medium"><FileClock className="h-4 w-4" /> Clinician review</p>
                <div className="flex flex-wrap gap-2">
                  <Button onClick={() => logAction.mutate('approve')}>Approve</Button>
                  <Button variant="outline" onClick={() => logAction.mutate('flag')}>Flag for second opinion</Button>
                  <Button variant="outline" onClick={() => logAction.mutate('note')}>Add note</Button>
                </div>
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
