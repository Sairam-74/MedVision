import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Upload, FileImage, AlertTriangle, Clock3, CircleAlert, ShieldCheck } from 'lucide-react';
import { createAnalysis, fetchAnalysisStatus } from '@/api/analyses';
import { PageHeader } from '@/components/layout/PageHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';

const maxSizeBytes = 10 * 1024 * 1024;
const allowedTypes = ['image/png', 'image/jpeg'];

export function UploadPage() {
  const navigate = useNavigate();
  const [fileName, setFileName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);

  const acceptedCopy = useMemo(() => 'Accepted formats: JPG or PNG only. Maximum size 10 MB.', []);

  const uploadMutation = useMutation({
    mutationFn: createAnalysis,
    onSuccess: (response) => {
      setAnalysisId(response.analysisId);
      setProgress(35);
    },
    onError: () => {
      setError('Upload failed. The study was not queued for analysis.');
      setProgress(0);
    },
  });

  const statusQuery = useQuery({
    queryKey: ['analysis-status', analysisId],
    queryFn: () => fetchAnalysisStatus(analysisId as string),
    enabled: Boolean(analysisId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === 'completed' || status === 'failed' || status === 'timed_out' ? false : 500;
    },
    refetchIntervalInBackground: true,
  });

  const currentStatus = statusQuery.data?.status ?? (uploadMutation.isPending ? 'processing' : analysisId ? 'queued' : 'idle');
  const busy = uploadMutation.isPending || Boolean(analysisId && ['queued', 'processing'].includes(currentStatus));
  useEffect(() => {
    if (statusQuery.isError) setError('Could not check analysis status. Open History to resume this case.');
  }, [statusQuery.isError]);

  useEffect(() => {
    if (!statusQuery.data) {
      return;
    }
    setProgress(statusQuery.data.progress);
    if (statusQuery.data.status === 'completed') {
      navigate(`/results/${statusQuery.data.analysisId}`, { replace: true });
    }
    if (statusQuery.data.status === 'failed' || statusQuery.data.status === 'timed_out') {
      setError(statusQuery.data.errorMessage ?? 'The prediction service could not complete this analysis.');
    }
  }, [navigate, statusQuery.data]);

  function validateFile(file: File) {
    if (!file.size) return 'The selected file is empty.';
    if (!allowedTypes.includes(file.type)) {
      return 'Unsupported file type. Upload JPG or PNG images only.';
    }
    if (file.size > maxSizeBytes) {
      return 'File is too large. Maximum size is 10 MB.';
    }
    return null;
  }

  function queueFile(file: File) {
    if (busy) return;
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      setAnalysisId(null);
      setProgress(0);
      return;
    }
    setError(null);
    setAnalysisId(null);
    setFileName(file.name);
    setProgress(15);
    uploadMutation.mutate(file);
  }

  return (
    <div className="space-y-6 clinical-grid">
      <PageHeader title="Image intake station" description="Upload a research X-ray and review the predicted regions alongside the original image." />
      <section className="workspace-hero grid gap-4 p-5 sm:grid-cols-3">
        {[['01 / Prepare', 'Use an original, de-identified research image. Avoid cropped screenshots and patient labels.'], ['02 / Predict', 'The service checks the image and produces a native-size segmentation overlay.'], ['03 / Inspect', 'Compare both views, check model identity and export the result for your research notes.']].map(([title, copy]) => <div key={title}><p className="eyebrow text-cyan-300">{title}</p><p className="mt-2 text-sm leading-6 text-slate-300">{copy}</p></div>)}
      </section>
      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
      <Card className="overflow-hidden shadow-soft">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" /> Create analysis
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <label
            className="flex min-h-72 cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-primary/50 bg-primary/5 p-8 text-center transition-colors hover:border-primary hover:bg-primary/10 focus-within:ring-2 focus-within:ring-ring"
            onDragOver={(event) => event.preventDefault()}
            onDrop={(event) => {
              event.preventDefault();
              const file = event.dataTransfer.files?.[0];
              if (file) {
                queueFile(file);
              }
            }}
          >
            <input
              type="file"
              disabled={busy}
              className="sr-only"
              accept=".jpg,.jpeg,.png,image/jpeg,image/png"
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (!file) return;
                queueFile(file);
                event.target.value = '';
              }}
            />
            <FileImage className="h-12 w-12 text-primary" />
            <p className="mt-4 text-lg font-medium">Drag and drop an X-ray image here</p>
            <p className="mt-1 max-w-md text-sm text-muted-foreground">{busy ? 'An analysis is in progress. Wait before uploading another image.' : 'Choose a research image. Do not upload patient-identifying information.'}</p>
            <div className="mt-4 flex flex-wrap justify-center gap-2 text-xs text-muted-foreground">
              <Badge variant="outline">JPG</Badge>
              <Badge variant="outline">PNG</Badge>
              <Badge variant="outline">Max 10 MB</Badge>
            </div>
          </label>
          <p className="text-sm text-muted-foreground">{acceptedCopy}</p>
          {fileName ? <p className="text-sm font-medium">Selected file: {fileName}</p> : null}
          {error ? (
            <Alert className="border-red-200 bg-red-50 text-red-950">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Upload error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : null}
          {currentStatus !== 'idle' ? <Progress value={progress} /> : null}
          {currentStatus === 'queued' ? <p className="flex items-center gap-2 text-sm text-muted-foreground"><Clock3 className="h-4 w-4" /> Study queued. Waiting for the prediction service.</p> : null}
          {currentStatus === 'processing' ? <p className="flex items-center gap-2 text-sm text-muted-foreground"><ShieldCheck className="h-4 w-4" /> Backend accepted the upload and is preparing inference.</p> : null}
          {currentStatus === 'timed_out' ? <p className="flex items-center gap-2 text-sm text-red-700"><CircleAlert className="h-4 w-4" /> Inference timed out. Retry or contact support.</p> : null}
          {currentStatus === 'completed' ? <p className="text-sm text-emerald-700">Analysis complete. Opening the review desk.</p> : null}
        </CardContent>
      </Card>
      <Card className="border-slate-200 bg-slate-950 text-slate-50 shadow-soft">
        <CardHeader>
          <CardTitle>Before you upload</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm text-slate-300">
          <div className="rounded-lg border border-cyan-400/30 bg-cyan-400/10 p-4">
            <p className="font-medium text-cyan-100">Research use only</p>
            <p className="mt-1">Predictions can miss fractures or highlight normal anatomy. This prototype is not a diagnosis.</p>
          </div>
          <div className="rounded-lg border border-slate-700 p-4">
            <p className="font-medium text-slate-100">Review the whole image</p>
            <p className="mt-1">Compare the original and overlay. An empty overlay does not establish that an image is healthy.</p>
          </div>
          <div className="rounded-lg border border-slate-700 p-4">
            <p className="font-medium text-slate-100">Resume from History</p>
            <p className="mt-1">Your saved analyses remain available after signing in again. Export result JSON for your research notes.</p>
          </div>
        </CardContent>
      </Card>
      </div>
      <Card><CardHeader><p className="section-kicker">What your result includes</p><CardTitle>A traceable analysis, ready to inspect</CardTitle></CardHeader><CardContent className="grid gap-5 text-sm sm:grid-cols-3"><div><p className="font-semibold">Original + overlay</p><p className="mt-2 leading-6 text-muted-foreground">Image proportions are preserved. Highlighted pixels show predicted regions; the original remains available for comparison.</p></div><div><p className="font-semibold">Model + geometry</p><p className="mt-2 leading-6 text-muted-foreground">The result includes a checkpoint identity, operating threshold and region measurements. Pixel geometry is not clinical severity.</p></div><div><p className="font-semibold">History + JSON export</p><p className="mt-2 leading-6 text-muted-foreground">Your completed cases are saved to your account. Export includes the mask and recorded model metadata, with unmeasured accuracy left empty.</p></div></CardContent></Card>
    </div>
  );
}
