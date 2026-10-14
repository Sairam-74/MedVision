import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { errorMessage } from '@/api/workflow';
import { useAuthStore } from '@/store/authStore';
import { Button } from '@/components/ui/button';
interface Model {
  id: string;
  status: string;
  checkpoint_sha: string;
  created_at: string;
  trained_at: string | null;
  promoted_at: string | null;
  metrics: string | null;
  previous_version: string | null;
}
interface Job {
  id: string;
  status: string;
  created_at: string;
  completed_at: string | null;
  error: string | null;
  candidate_id: string | null;
}
export function ModelManagement() {
  const user = useAuthStore((s) => s.user);
  const admin = user?.role === 'admin';
  const review = admin || user?.role === 'clinician';
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const current = useQuery({
    queryKey: ['model-current'],
    queryFn: async () =>
      (
        await apiClient.get<{
          model: Model | null;
          feedback_count: number;
          threshold: number;
          metrics: unknown;
        }>('/models/current')
      ).data,
    refetchInterval: 10000,
  });
  const models = useQuery({
    queryKey: ['model-history'],
    queryFn: async () => (await apiClient.get<Model[]>('/models/history')).data,
    refetchInterval: 10000,
  });
  const jobs = useQuery({
    queryKey: ['training-jobs'],
    queryFn: async () => (await apiClient.get<Job[]>('/retraining/jobs')).data,
    enabled: review,
    refetchInterval: 5000,
  });
  async function action(path: string, data: unknown = {}) {
    setBusy(true);
    setError('');
    try {
      await apiClient.post(path, data);
      await Promise.all([current.refetch(), models.refetch(), jobs.refetch()]);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="space-y-3 rounded-xl border p-4">
      <h2 className="font-bold">
        Production model and reviewed-feedback training
      </h2>
      {current.isError ? (
        <p role="alert">Model registry unavailable.</p>
      ) : (
        <>
          <p>
            Production: {current.data?.model?.id ?? 'Unavailable'} · Feedback:{' '}
            {current.data?.feedback_count ?? 'Unavailable'} · Confirmed-image
            threshold: {current.data?.threshold ?? 'Unavailable'}
          </p>
          <p>
            Latest production training:{' '}
            {current.data?.model?.trained_at
              ? new Date(current.data.model.trained_at).toLocaleString()
              : 'Not recorded'}
          </p>
          <p>
            Calibration and robustness: unavailable unless recorded by
            evaluation. Research-only segmentation; subtype and case confidence
            unavailable.
          </p>
        </>
      )}
      {admin && (
        <Button
          disabled={busy}
          onClick={() =>
            action('/retraining/jobs', { epochs: 2, smoke: false })
          }
        >
          Start authorized candidate training
        </Button>
      )}
      {error && <p role="alert">{error}</p>}
      {jobs.isError && review && <p>Training job history unavailable.</p>}
      {jobs.data?.map((j) => (
        <article key={j.id} className="border p-3">
          <p>
            {j.id} · {j.status} · {new Date(j.created_at).toLocaleString()}
          </p>
          <p>{j.error}</p>
          {admin && ['failed', 'blocked', 'interrupted'].includes(j.status) && (
            <Button
              disabled={busy}
              onClick={() => action(`/retraining/jobs/${j.id}/retry`)}
            >
              Retry safely
            </Button>
          )}
        </article>
      ))}
      {models.data?.map((m) => (
        <details key={m.id}>
          <summary>
            {m.id} · {m.status} · {new Date(m.created_at).toLocaleString()}
          </summary>
          <p>Checkpoint SHA-256: {m.checkpoint_sha}</p>
          <pre className="whitespace-pre-wrap text-xs">
            {m.metrics
              ? JSON.stringify(JSON.parse(m.metrics), null, 2)
              : 'Evaluation metrics unavailable'}
          </pre>
          {admin && m.status === 'candidate_ready' && (
            <Button
              disabled={busy}
              onClick={() => action(`/models/${m.id}/promote`)}
            >
              Promote validated candidate
            </Button>
          )}
          {admin && m.status === 'previous' && (
            <Button
              disabled={busy}
              onClick={() => action(`/models/${m.id}/rollback`)}
            >
              Roll back to this model
            </Button>
          )}
        </details>
      ))}
      <p className="text-xs">
        Candidates run in a separate process and cannot overwrite production.
        Promotion requires the frozen 463-image validation targets, improved
        overlap/localization and verified partition independence. The current
        manifest does not establish patient independence, so promotion remains
        gated.
      </p>
    </section>
  );
}
