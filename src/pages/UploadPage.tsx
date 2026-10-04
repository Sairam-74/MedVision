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
    if (!allowedTypes.includes(file.type)) {
      return 'Unsupported file type. Upload JPG or PNG images only.';
    }
    if (file.size > maxSizeBytes) {
      return 'File is too large. Maximum size is 10 MB.';
    }
    return null;
  }

  function queueFile(file: File) {
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      setAnalysisId(null);
      setProgress(0);
      return;
    }
    setError(null);
    setFileName(file.name);
    setProgress(15);
    uploadMutation.mutate(file);
  }

  return (
    <div className="space-y-6 clinical-grid">
      <PageHeader title="Image intake station" description="Upload an X-ray to create an analysis job, then let the backend hand it to the Python prediction service." />
      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
      <Card className="overflow-hidden border-slate-200 shadow-soft">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" /> Create analysis
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <label
            className="flex min-h-64 cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-slate-300 bg-white p-8 text-center transition-colors hover:border-primary hover:bg-cyan-50/40"
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
              className="sr-only"
              accept=".jpg,.jpeg,.png,image/jpeg,image/png"
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (!file) return;
                queueFile(file);
              }}
            />
            <FileImage className="h-12 w-12 text-primary" />
            <p className="mt-4 text-lg font-medium">Drag and drop an X-ray image here</p>
            <p className="mt-1 max-w-md text-sm text-muted-foreground">The browser sends the image to the web backend. The backend queues the Python model service server-side.</p>
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
          <CardTitle>Prediction service path</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm text-slate-300">
          <div className="rounded-lg border border-cyan-400/30 bg-cyan-400/10 p-4">
            <p className="font-medium text-cyan-100">POST /analyses</p>
            <p className="mt-1">Creates an authenticated upload job. The browser never sees the model bearer token.</p>
          </div>
          <div className="rounded-lg border border-slate-700 p-4">
            <p className="font-medium text-slate-100">GET /analyses/:id/status</p>
            <p className="mt-1">Polls queued, processing, completed, failed, or timed-out state.</p>
          </div>
          <div className="rounded-lg border border-slate-700 p-4">
            <p className="font-medium text-slate-100">GET /analyses/:id</p>
            <p className="mt-1">Returns original image, overlay/mask, severity, threshold, and optional Dice/IoU metrics.</p>
          </div>
        </CardContent>
      </Card>
      </div>
    </div>
  );
}
