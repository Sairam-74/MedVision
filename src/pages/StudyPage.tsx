import { useEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import {
  getStudy,
  uploadView,
  generateReport,
  saveReport,
  feedbackList,
  submitFeedback,
  uploadCorrection,
  confirmCorrection,
  errorMessage,
} from '@/api/workflow';
import type { Report, Feedback, StudyImage, Study } from '@/api/workflow';
import { XrayViewer } from '@/components/workflow/XrayViewer';
import { Button } from '@/components/ui/button';
import { PageHeader } from '@/components/layout/PageHeader';
import { useAuthStore } from '@/store/authStore';
const localTime = (stamp: string | null | undefined) =>
  stamp ? new Date(stamp).toLocaleString() : 'Unavailable';
function FeedbackPanel({ image }: { image: StudyImage }) {
  const [correct, setCorrect] = useState(true);
  const [category, setCategory] = useState('False positive');
  const [comments, setComments] = useState('');
  const [corrected, setCorrected] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState<Feedback | null>(null);
  const [mask, setMask] = useState<File | null>(null);
  const [fracture, setFracture] = useState(true);
  const [consent, setConsent] = useState(false);
  const [partition, setPartition] = useState(false);
  const q = useQuery({
    queryKey: ['feedback', image.analysis_id],
    queryFn: () => feedbackList(image.analysis_id),
  });
  async function submit() {
    setBusy(true);
    setError('');
    try {
      const f = await submitFeedback(image.analysis_id, {
        correct,
        category: correct ? '' : category,
        comments,
        corrected_findings: corrected
          ? { radiologist_findings: corrected }
          : {},
      });
      setSelected(f);
      await q.refetch();
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }
  async function confirm() {
    if (!selected) return;
    setBusy(true);
    setError('');
    try {
      if (mask) await uploadCorrection(selected.id, mask);
      await confirmCorrection(selected.id, fracture, consent, partition);
      setSelected(null);
      await q.refetch();
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="space-y-3 rounded-xl border p-4">
      <h3 className="font-bold">Radiologist feedback</h3>
      <label>
        Assessment
        <select
          aria-label="AI assessment"
          className="block"
          value={correct ? 'correct' : 'incorrect'}
          onChange={(e) => setCorrect(e.target.value === 'correct')}
        >
          <option value="correct">AI correct</option>
          <option value="incorrect">AI incorrect</option>
        </select>
      </label>
      {!correct && (
        <label>
          Error category
          <select
            aria-label="Error category"
            className="block"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          >
            {[
              'False positive',
              'False negative',
              'Wrong localization',
              'Wrong bone',
              'Wrong fracture type',
              'Wrong displacement',
              'Incorrect segmentation',
              'Misleading confidence',
              'Other',
            ].map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
        </label>
      )}
      <label>
        Comments
        <textarea
          aria-label="Feedback comments"
          className="block w-full border p-2"
          maxLength={4000}
          value={comments}
          onChange={(e) => setComments(e.target.value)}
        />
      </label>
      <label>
        Corrected findings
        <textarea
          aria-label="Feedback corrected findings"
          className="block w-full border p-2"
          maxLength={1000}
          value={corrected}
          onChange={(e) => setCorrected(e.target.value)}
        />
      </label>
      <Button disabled={busy} onClick={submit}>
        Submit preliminary feedback
      </Button>
      {error && <p role="alert">{error}</p>}
      {selected && (
        <fieldset className="space-y-2 border p-3">
          <legend>Confirm a research training annotation</legend>
          <p>
            Only documented training-cohort images with research permission
            enter retraining. Other confirmed annotations remain review records.
            Incorrect findings require a corrected native-size PNG mask (0/255).
          </p>
          <label>
            Corrected segmentation mask
            <input
              aria-label="Corrected segmentation mask"
              type="file"
              accept="image/png"
              onChange={(e) => setMask(e.target.files?.[0] ?? null)}
            />
          </label>
          <label className="block">
            <input
              type="checkbox"
              checked={fracture}
              onChange={(e) => setFracture(e.target.checked)}
            />{' '}
            Confirmed fracture region present
          </label>
          <label className="block">
            <input
              type="checkbox"
              checked={consent}
              onChange={(e) => setConsent(e.target.checked)}
            />{' '}
            De-identified research use permitted
          </label>
          <label className="block">
            <input
              type="checkbox"
              checked={partition}
              onChange={(e) => setPartition(e.target.checked)}
            />{' '}
            Training partition verified; no validation/test overlap
          </label>
          <Button disabled={busy} onClick={confirm}>
            Confirm reviewed annotation
          </Button>
        </fieldset>
      )}
      {q.isError && <p role="alert">Feedback history unavailable.</p>}
      <ul className="space-y-2">
        {q.data?.map((f) => (
          <li key={f.id}>
            {f.correct ? 'Correct' : f.category} ·{' '}
            {f.confirmed ? 'Confirmed annotation' : 'Preliminary'} ·{' '}
            {localTime(f.created_at)}
            <p>{f.comments}</p>
            {!f.confirmed && (
              <button
                onClick={() => {
                  setSelected(f);
                  setMask(null);
                  setConsent(false);
                  setPartition(false);
                }}
              >
                Review annotation
              </button>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
function ReportEditor({
  studyId,
  report,
  onSaved,
  study,
}: {
  studyId: string;
  report: Report | null;
  onSaved: () => void;
  study: Study;
}) {
  const [draft, setDraft] = useState<Report | null>(report);
  const [corrections, setCorrections] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    setDraft(report);
    setCorrections(
      report
        ? String(JSON.parse(report.corrections).radiologist?.findings ?? '')
        : '',
    );
  }, [report]);
  async function action(operation: string) {
    setError('');
    setBusy(true);
    try {
      if (operation === 'generate') setDraft(await generateReport(studyId));
      else if (draft)
        setDraft(
          await saveReport(
            studyId,
            draft,
            operation,
            corrections ? { findings: corrections } : {},
          ),
        );
      onSaved();
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section id="radiology-report" className="space-y-3 rounded-xl border p-4">
      <h3 className="font-bold">
        RADIOLOGY REPORT —{' '}
        {draft?.status === 'final'
          ? 'Radiologist-finalized'
          : 'Editable AI-assisted draft'}
      </h3>
      <div className="report-context">
        <h4 className="font-bold">Patient information</h4>
        <p>
          {study.patient.name} · {study.patient.identifier} · Age{' '}
          {study.patient.age ?? 'not collected'} · Gender {study.patient.gender}
        </p>
        <h4 className="mt-3 font-bold">Examination</h4>
        <p>
          {study.examination_date} · {study.body_part} · {study.laterality} ·
          Views {study.images.map((i) => i.view_type).join(', ')}
        </p>
        <p>Clinical history: {study.clinical_history || 'Not collected'}</p>
        <p>
          Referring physician: {study.referring_physician || 'Not collected'}
        </p>
      </div>
      {!draft ? (
        <Button disabled={busy} onClick={() => action('generate')}>
          Generate report draft
        </Button>
      ) : (
        <>
          <p>
            Revision {draft.revision} · Updated {localTime(draft.updated_at)} ·
            Finalized {localTime(draft.finalized_at)}
          </p>
          <div className="report-edit-controls">
            <label>
              Findings
              <textarea
                aria-label="Report findings"
                className="block min-h-32 w-full border p-2"
                disabled={draft.status === 'final'}
                value={draft.findings}
                onChange={(e) =>
                  setDraft({ ...draft, findings: e.target.value })
                }
              />
            </label>
            <label>
              Impression
              <textarea
                aria-label="Report impression"
                className="block min-h-24 w-full border p-2"
                disabled={draft.status === 'final'}
                value={draft.impression}
                onChange={(e) =>
                  setDraft({ ...draft, impression: e.target.value })
                }
              />
            </label>
            <label>
              AI suggestions
              <select
                aria-label="AI suggestions"
                className="block"
                disabled={draft.status === 'final'}
                value={draft.ai_decision}
                onChange={(e) =>
                  setDraft({ ...draft, ai_decision: e.target.value })
                }
              >
                {['pending', 'accepted', 'rejected', 'corrected'].map((v) => (
                  <option key={v}>{v}</option>
                ))}
              </select>
            </label>
            <label>
              Radiologist corrections
              <textarea
                aria-label="Report corrections"
                className="block w-full border p-2"
                disabled={draft.status === 'final'}
                maxLength={1000}
                value={corrections}
                onChange={(e) => setCorrections(e.target.value)}
              />
            </label>
            <div className="flex flex-wrap gap-2">
              {draft.status === 'final' ? (
                <Button disabled={busy} onClick={() => action('reopen')}>
                  Reopen report
                </Button>
              ) : (
                <>
                  <Button disabled={busy} onClick={() => action('save')}>
                    Save draft
                  </Button>
                  <Button
                    variant="outline"
                    disabled={busy}
                    onClick={() => action('generate')}
                  >
                    Regenerate AI draft (keeps history)
                  </Button>
                  <Button
                    disabled={busy || draft.ai_decision === 'pending'}
                    onClick={() => action('finalize')}
                  >
                    Finalize report
                  </Button>
                </>
              )}
              <Button
                variant="outline"
                onClick={() => {
                  const blob = new Blob([JSON.stringify(draft, null, 2)], {
                    type: 'application/json',
                  });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `${studyId}-report.json`;
                  a.click();
                  URL.revokeObjectURL(url);
                }}
              >
                Export report JSON
              </Button>
              <Button variant="outline" onClick={() => window.print()}>
                Print / Save PDF
              </Button>
            </div>
            <details>
              <summary>
                Report audit history ({draft.versions.length} revisions)
              </summary>
              {draft.versions.map((v) => (
                <div key={v.revision} className="my-3 border p-2">
                  <p>
                    Revision {v.revision} · {localTime(v.created_at)} · Reviewer{' '}
                    {v.author_id}
                  </p>
                  <pre className="whitespace-pre-wrap text-xs">
                    {v.snapshot}
                  </pre>
                </div>
              ))}
            </details>
          </div>
          <div className="print-only">
            <h4>Findings</h4>
            <p className="whitespace-pre-wrap">{draft.findings}</p>
            <h4>Impression</h4>
            <p className="whitespace-pre-wrap">{draft.impression}</p>
            <p>
              AI suggestions: {draft.ai_decision}. Reviewer:{' '}
              {draft.versions.at(-1)?.author_id ?? 'Unavailable'}
            </p>
          </div>
          <h4 className="font-bold">AI-assisted findings — original draft</h4>
          <p className="whitespace-pre-wrap">
            {JSON.parse(draft.versions[0]?.snapshot ?? '{}').findings ??
              'Unavailable'}
          </p>
          <p className="text-xs">
            Model versions:{' '}
            {JSON.parse(draft.corrections).model_versions?.join(', ') ??
              'Unavailable'}
          </p>
        </>
      )}
      {error && <p role="alert">{error}</p>}
      <p className="text-xs">
        AI drafts are research suggestions. Finalization records an authorized
        reviewer action and never occurs automatically.
      </p>
    </section>
  );
}
export function StudyPage() {
  const { studyId = '' } = useParams();
  const query = useQuery({
    queryKey: ['study', studyId],
    queryFn: () => getStudy(studyId),
    refetchInterval: (q) =>
      q.state.data?.images.some((i) =>
        ['queued', 'processing'].includes(i.analysis.status),
      )
        ? 2000
        : false,
  });
  const user = useAuthStore((s) => s.user);
  const canReview = user?.role === 'clinician' || user?.role === 'admin';
  const [selected, setSelected] = useState('');
  const [view, setView] = useState('AP');
  const [file, setFile] = useState<File | null>(null);
  const [compare, setCompare] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const fileInput = useRef<HTMLInputElement>(null);
  const study = query.data;
  const selectedImage =
    study?.images.find((i) => i.id === selected) ?? study?.images[0];
  async function upload() {
    if (!file) return;
    setBusy(true);
    setError('');
    try {
      if (!['image/jpeg', 'image/png'].includes(file.type) || file.size === 0) {
        setError('Choose a nonempty JPG or PNG image.');
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        setError('File is too large. Maximum size is 10 MB.');
        return;
      }
      await uploadView(studyId, view, file);
      setFile(null);
      if (fileInput.current) fileInput.current.value = '';
      await query.refetch();
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }
  if (!study)
    return (
      <p>
        {query.isError
          ? 'Study could not be loaded. Check access and connection.'
          : 'Loading study…'}
        <button onClick={() => query.refetch()}>Retry</button>
      </p>
    );
  return (
    <div className="space-y-6">
      <PageHeader
        title={`${study.patient.name} · ${study.patient.identifier}`}
        description={`${study.body_part} · ${study.laterality} · Examination ${study.examination_date}`}
        actions={
          <Button asChild>
            <Link to="/upload">New study</Link>
          </Button>
        }
      />
      <section className="rounded-xl border p-4">
        <p>
          Age {study.patient.age ?? 'not collected'} · Gender{' '}
          {study.patient.gender}
        </p>
        <p>Clinical history: {study.clinical_history || 'Not collected'}</p>
        <p>
          Referring physician: {study.referring_physician || 'Not collected'} ·
          Created {localTime(study.created_at)}
        </p>
        <p>
          Views:{' '}
          {study.images.map((i) => i.view_type).join(', ') || 'None uploaded'}
        </p>
      </section>
      <section className="space-y-3 rounded-xl border p-4">
        <h2 className="font-bold">Upload another view to this study</h2>
        <label>
          View type
          <select
            aria-label="View type"
            value={view}
            onChange={(e) => setView(e.target.value)}
          >
            {['AP', 'Lateral', 'Oblique'].map((v) => (
              <option key={v}>{v}</option>
            ))}
          </select>
        </label>
        <input
          ref={fileInput}
          aria-label="Study X-ray"
          type="file"
          accept="image/png,image/jpeg"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
        <Button disabled={busy || !file} onClick={upload}>
          Upload and analyze view
        </Button>
        {error && <p role="alert">{error}</p>}
        <p>
          Each view is analyzed independently; multi-view fusion is not
          performed. JPG/PNG only, maximum 10 MB.
        </p>
      </section>
      {study.images.length > 0 && (
        <>
          <label>
            Select study view
            <select
              aria-label="Select study view"
              value={selectedImage?.id ?? ''}
              onChange={(e) => setSelected(e.target.value)}
            >
              {study.images.map((i) => (
                <option key={i.id} value={i.id}>
                  {i.view_type} · {i.analysis.status} ·{' '}
                  {localTime(i.uploaded_at)}
                </option>
              ))}
            </select>
          </label>
          <label>
            <input
              type="checkbox"
              checked={compare}
              onChange={(e) => setCompare(e.target.checked)}
            />{' '}
            Compare all completed views
          </label>
          <div className={compare ? 'grid gap-4 lg:grid-cols-2' : 'space-y-4'}>
            {(compare
              ? study.images
              : selectedImage
                ? [selectedImage]
                : []
            ).map((image) => (
              <section key={image.id} className="space-y-3">
                <h2 className="font-bold">
                  {image.view_type} — {image.analysis.status}
                </h2>
                {image.result ? (
                  <>
                    <XrayViewer result={image.result} />
                    <dl className="grid grid-cols-2 gap-2 rounded border p-3">
                      <dt>Fracture presence</dt>
                      <dd>
                        {image.result.fracturePresence ??
                          'Uncertain — radiologist review required'}
                      </dd>
                      <dt>Model version</dt>
                      <dd>
                        {image.result.modelVersion ??
                          image.result.modelSha256 ??
                          'Unavailable'}
                      </dd>
                      <dt>Completed</dt>
                      <dd>{localTime(image.result.analysisCompletedAt)}</dd>
                      <dt>Segmented regions</dt>
                      <dd>
                        {image.result.severityFeatures?.componentCount ??
                          'Unavailable'}
                      </dd>
                      <dt>Confidence</dt>
                      <dd>
                        {image.result.confidence ??
                          'Unavailable; case confidence not calibrated'}
                      </dd>
                      {[
                        ['Bone', image.result.bone],
                        ['Location', image.result.location],
                        ['Fracture type', image.result.fractureType],
                        ['Displacement', image.result.displacement],
                        ['Angulation', image.result.angulation],
                      ].map(([label, value]) => (
                        <div className="contents" key={label}>
                          <dt>{label}</dt>
                          <dd>{value ?? 'Not determined'}</dd>
                        </div>
                      ))}
                    </dl>
                    {canReview && <FeedbackPanel image={image} />}
                  </>
                ) : (
                  <p role={image.error ? 'alert' : undefined}>
                    {image.error ??
                      'Inference pending. Status updates automatically.'}
                  </p>
                )}
              </section>
            ))}
          </div>
        </>
      )}
      {canReview ? (
        <ReportEditor
          study={study}
          studyId={study.id}
          report={study.report}
          onSaved={() => query.refetch()}
        />
      ) : (
        <p>Report editing and feedback require a clinician account.</p>
      )}
      <p>
        Research prototype. An empty mask does not rule out fracture. No
        clinical diagnosis is established by AI.
      </p>
    </div>
  );
}
