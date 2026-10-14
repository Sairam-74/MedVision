import { StudySearch } from '@/components/workflow/StudySearch';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowRight, ScanLine, Layers3, FileJson, FileImage, Activity, FlaskConical } from 'lucide-react';
import { fetchAnalyses } from '@/api/analyses';
import { fetchResearchStatus } from '@/api/research';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { formatRelative } from '@/utils/format';

export function DashboardPage() {
  const analysesQuery = useQuery({ queryKey: ['analyses'], queryFn: fetchAnalyses, refetchInterval: 5000 });
  const research = useQuery({ queryKey: ['research'], queryFn: fetchResearchStatus, refetchInterval: 30000 });
  const analyses = analysesQuery.data ?? [];
  const completed = analyses.filter(a => a.status === 'completed').length;
  const active = analyses.filter(a => ['queued', 'processing'].includes(a.status)).length;
  const latest = research.data?.runs.find(r => r.status === 'training');
  return (
    <div className="space-y-6">
      <StudySearch />
      <section className="workspace-hero grid gap-8 p-6 md:p-8 xl:grid-cols-[1.3fr_1fr]">
        <div>
          <p className="eyebrow text-cyan-300">Visual intelligence · Research workflow</p>
          <h2 className="mt-4 text-3xl font-bold tracking-tight sm:text-4xl">Home dashboard</h2>
          <p className="mt-3 max-w-xl text-base leading-7 text-slate-300">Turn an X-ray into inspectable evidence. Compare native-size images and predicted regions, revisit every case, and follow the experiments behind the model.</p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Button asChild className="bg-cyan-300 font-bold text-slate-950 hover:bg-cyan-200"><Link to="/upload"><ScanLine className="h-4 w-4" /> Upload X-ray <ArrowRight className="h-4 w-4" /></Link></Button>
            <Button asChild className="border border-slate-500 bg-white/5 text-white hover:bg-white/15"><Link to="/research">View research</Link></Button>
          </div>
          <p className="mt-5 text-xs text-slate-400">Research use only · An empty overlay does not rule out a fracture.</p>
        </div>
        <div className="rounded-xl border border-white/20 bg-slate-950/35 p-5">
          <p className="eyebrow text-cyan-200">Your workspace at a glance</p>
          <div className="mt-5 grid grid-cols-3 gap-3">
            {[['Saved cases', analysesQuery.isSuccess ? analyses.length : '—'], ['Completed', analysesQuery.isSuccess ? completed : '—'], ['In progress', analysesQuery.isSuccess ? active : '—']].map(([title, value]) => <div key={title}><p className="text-3xl font-bold tabular-nums text-white">{value}</p><p className="mt-1 text-xs text-slate-300">{title}</p></div>)}
          </div>
          <div className="mt-6 border-t border-white/15 pt-4">
            <p className="flex items-center gap-2 text-sm font-semibold"><Activity className="h-4 w-4 text-cyan-300" /> Experiment activity</p>
            <p className="mt-2 text-sm text-slate-300">{latest ? `${latest.label} · epoch ${latest.epoch}${latest.batch && latest.batches ? ` · batch ${latest.batch}/${latest.batches}` : ''}` : research.isError ? 'Research status unavailable. Open Research to retry.' : research.isLoading ? 'Reading recorded experiment status…' : 'Open Research for completed and queued experiments.'}</p>
            <p className="mt-2 text-xs text-slate-400">Live recorded progress. The original diagnostic model serves uploads.</p>
          </div>
        </div>
      </section>
      <section className="grid gap-4 md:grid-cols-3">
        {[{ icon: ScanLine, step: '01', title: 'Upload a research image', text: 'Use a de-identified JPG or PNG. The image is checked before it enters the prediction queue.' }, { icon: Layers3, step: '02', title: 'Inspect the prediction', text: 'Compare the original and overlay at the same aspect ratio. Highlights show model output, not a confirmed diagnosis.' }, { icon: FileJson, step: '03', title: 'Keep the evidence', text: 'Reopen cases from your private History. Export the mask, model identity and measured geometry as JSON.' }].map(item => <Card key={item.step} className="feature-tile"><CardContent className="p-5"><div className="flex justify-between"><item.icon className="h-6 w-6 text-primary" /><span className="text-sm font-bold text-muted-foreground">{item.step}</span></div><h3 className="mt-4 text-base font-bold">{item.title}</h3><p className="mt-2 text-sm leading-6 text-muted-foreground">{item.text}</p></CardContent></Card>)}
      </section>
      <div className="grid gap-6 xl:grid-cols-[1.4fr_1fr]">
        <Card>
          <CardHeader className="flex-row items-center justify-between gap-3"><div><p className="section-kicker">Case library</p><CardTitle className="mt-1">Recent analyses</CardTitle></div><Button variant="outline" asChild><Link to="/history">View all</Link></Button></CardHeader>
          <CardContent className="space-y-3">
            {analysesQuery.isLoading ? <p>Loading your case library…</p> : analysesQuery.isError ? <div role="alert"><p>Could not load analyses.</p><Button className="mt-2" onClick={() => analysesQuery.refetch()}>Retry</Button></div> : analyses.length ? analyses.slice(0, 4).map(a => <Link key={a.id} to={a.status === 'completed' ? `/results/${a.id}` : '/history'} className="flex items-center gap-3 rounded-xl border border-border p-3 transition-colors hover:bg-muted"><div className="rounded-lg bg-primary/10 p-3 text-primary"><FileImage className="h-5 w-5" /></div><div className="min-w-0 flex-1"><p className="truncate text-sm font-semibold">{a.fileName}</p><p className="mt-1 text-xs text-muted-foreground">{formatRelative(a.createdAt)}</p></div><Badge variant={a.status === 'completed' ? 'success' : a.status === 'failed' || a.status === 'timed_out' ? 'destructive' : 'secondary'} className="shrink-0 capitalize">{a.status.replace('_', ' ')}</Badge></Link>) : <div className="rounded-xl border border-dashed border-border p-6"><FileImage className="h-8 w-8 text-primary" /><h3 className="mt-3 font-bold">Your first case starts here</h3><p className="mt-2 text-sm leading-6 text-muted-foreground">Upload an image to create a persistent case with an original, prediction overlay and exportable result.</p><Button className="mt-4" asChild><Link to="/upload">Upload first X-ray</Link></Button></div>}
          </CardContent>
        </Card>
        <Card className="border-primary/30"><CardHeader><p className="section-kicker">Behind the prediction</p><CardTitle>Built around measurable evidence</CardTitle></CardHeader><CardContent><div className="grid grid-cols-2 gap-4"><div><p className="text-3xl font-bold text-primary">{research.data?.dataset.available ? research.data.dataset.total.toLocaleString() : '—'}</p><p className="mt-1 text-xs text-muted-foreground">Eligible audited images · v2</p></div><div><p className="text-3xl font-bold text-primary">{research.data?.dataset.available ? research.data.dataset.validation : '—'}</p><p className="mt-1 text-xs text-muted-foreground">Validation images</p></div></div><p className="mt-5 text-sm leading-6 text-muted-foreground">Attention U-Net predicts a segmentation mask. Validation tracks overlap, missed positive cases and false alarms on normal images; all three matter.</p><div className="mt-4 rounded-lg bg-muted p-3 text-xs leading-5">Final model selection and the reserved test are pending. Historical checkpoint exposure is unknown.</div><Link className="mt-5 flex items-center gap-2 text-sm font-bold text-primary" to="/research"><FlaskConical className="h-4 w-4" /> Open research & methodology <ArrowRight className="h-4 w-4" /></Link></CardContent></Card>
      </div>
    </div>
  );
}
