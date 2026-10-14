import { XrayViewer } from '@/components/workflow/XrayViewer';
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

export function ResultsPage() {
  const { analysisId = '' } = useParams();
  const { data, isLoading, isError, refetch } = useQuery({ queryKey: ['analysis', analysisId], queryFn: () => fetchAnalysisById(analysisId), enabled: Boolean(analysisId) });
  const canApprove = false;
  const logAction = useMutation({ mutationFn: async (action: string) => ({ action }) });
  const statusColor = useMemo(() => {
    if (!data) return 'secondary';
    return data.fractureStatus === 'fracture' ? 'destructive' : data.fractureStatus === 'no_fracture' ? 'secondary' : 'warning';
  }, [data]);

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading result…</p>;
  }

  if (!data) {
    return <div><p>{isError ? 'Could not load this result. Check your connection and access to this case.' : 'Result not found.'}</p><Button onClick={() => refetch()}>Retry</Button></div>;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Prediction result"
        description="Compare the original X-ray and predicted regions from this research prototype."
        actions={
          <>
            <Button variant="outline" asChild>
              <Link to="/upload">New analysis</Link>
            </Button>
            <Button variant="outline" onClick={() => {
              const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }));
              const link = document.createElement('a');
              link.href = url;
              link.download = `${data?.analysisId ?? 'medvision'}-result.json`;
              link.click();
              URL.revokeObjectURL(url);
            }}>Export result JSON</Button>
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
      <section className="workspace-hero grid gap-4 p-5 sm:grid-cols-3">
        <div><p className="eyebrow text-cyan-300">Prediction output</p><p className="mt-2 text-lg font-bold">{data.fractureStatus === 'no_fracture' ? 'No region highlighted' : data.fractureStatus === 'fracture' ? 'Region highlighted' : 'Review required'}</p><p className="mt-1 text-xs leading-5 text-slate-300">Model output, not a confirmed diagnosis.</p></div>
        <div><p className="eyebrow text-cyan-300">Image dimensions</p><p className="mt-2 text-lg font-bold">{data.maskShape ? `${data.maskShape[1]} × ${data.maskShape[0]} px` : 'Not recorded'}</p><p className="mt-1 text-xs leading-5 text-slate-300">Native-size mask · original aspect ratio.</p></div>
        <div><p className="eyebrow text-cyan-300">Decision threshold</p><p className="mt-2 text-lg font-bold">{data.calibratedThreshold === undefined ? 'Not recorded' : data.calibratedThreshold.toFixed(2)}</p><p className="mt-1 text-xs leading-5 text-slate-300">Probability cutoff; validation provenance determines calibration.</p></div>
      </section>
      <div className="grid gap-6 lg:grid-cols-[1.4fr_0.9fr]">
        <Card className="overflow-hidden border-slate-200 shadow-soft">
          <CardHeader className="border-b border-border bg-slate-950 text-slate-50">
            <div className="flex items-center justify-between gap-3">
              <CardTitle className="flex items-center gap-2">
                <ScanLine className="h-5 w-5 text-cyan-300" /> Evidence viewer
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent className="bg-muted p-4">
            <XrayViewer result={data} />
          </CardContent>
        </Card>
        <Card className="border-slate-200 shadow-soft">
          <CardHeader>
            <div className="flex items-start justify-between gap-3">
              <div>
                <CardTitle className="flex items-center gap-2"><Activity className="h-5 w-5" /> Result summary</CardTitle>
                <p className="text-sm text-muted-foreground">Case {data.analysisId}</p>
              </div>
              <Badge variant={statusColor as never}>{data.fractureStatus === 'no_fracture' ? 'No predicted region' : data.fractureStatus === 'fracture' ? 'Predicted region' : 'Needs review'}</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 text-sm">
              <div>
                <p className="text-muted-foreground">Clinical severity</p>
                <p className="font-medium capitalize">Not determined</p>
                <p className="text-xs text-muted-foreground">Not supported by the current segmentation model.</p>
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
      <Card><CardHeader><p className="section-kicker">Provenance & interpretation</p><CardTitle>Read the evidence behind this case</CardTitle></CardHeader><CardContent className="grid gap-5 md:grid-cols-2"><div><p className="text-sm font-semibold">Recorded model identity</p><p className="mt-2 break-all rounded-lg bg-muted p-3 font-mono text-xs leading-6">{data.modelSha256 ?? 'Not recorded for this historical case'}</p><p className="mt-2 text-xs text-muted-foreground">Checkpoint SHA-256 identifies the weights used for this result.</p></div><div><p className="text-sm font-semibold">What the overlay can establish</p><p className="mt-2 text-sm leading-7 text-muted-foreground">Highlighted pixels are predicted regions. A normal image may receive highlights, and a fractured image may receive none. No reference annotation is available for this upload, so overlap and accuracy are unmeasured.</p><Link className="mt-3 inline-block text-sm font-semibold text-primary" to="/research">Read validation results & methodology →</Link></div></CardContent></Card>
    </div>
  );
}
