import { Outlet } from 'react-router-dom';
import { ScanLine, Layers3, FileJson, ArrowDown } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export function AuthShell() {
  return (
    <main className="min-h-screen px-4 py-10 lg:px-8">
      <div className="mx-auto grid min-h-[calc(100vh-5rem)] max-w-7xl gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <section className="workspace-hero p-8 lg:p-12">
          <div className="max-w-xl space-y-6">
            <p className="eyebrow flex items-center gap-3 text-cyan-300"><ScanLine className="h-6 w-6" /> MedVision AI · Research workspace</p>
            <h1 className="text-4xl font-bold leading-tight lg:text-5xl">From X-ray to<br />visible evidence.</h1>
            <p className="text-base leading-7 text-slate-300">
              A focused workspace for fracture segmentation. Inspect predicted regions, preserve the original image, and understand the experiments behind every result.
            </p>
            <div className="grid gap-3 text-sm text-slate-200 sm:grid-cols-2">
              <Card className="border-white/10 bg-white/5 text-slate-50 shadow-none">
                <CardHeader>
                  <CardTitle className="text-base">Secure sessions</CardTitle>
                  <CardDescription className="text-slate-300">Sign in to access your saved analyses. Sign out to end access from this session.</CardDescription>
                </CardHeader>
              </Card>
              <Card className="border-white/10 bg-white/5 text-slate-50 shadow-none">
                <CardHeader>
                  <CardTitle className="text-base">Research history</CardTitle>
                  <CardDescription className="text-slate-300">Revisit your uploaded images and export result JSON for research notes.</CardDescription>
                </CardHeader>
              </Card>
            </div>
            <div className="space-y-3 rounded-xl border border-white/20 bg-slate-950/30 p-5">
              <p className="eyebrow text-cyan-200">One connected research workflow</p>
              {[{ icon: ScanLine, title: 'Upload', copy: 'De-identified JPG or PNG · up to 10 MB' }, { icon: Layers3, title: 'Inspect', copy: 'Original image + segmentation overlay' }, { icon: FileJson, title: 'Document', copy: 'Persistent cases + exportable result evidence' }].map((step, i) => <div key={step.title}><div className="flex gap-3"><step.icon className="mt-1 h-5 w-5 shrink-0 text-cyan-300" /><div><p className="text-sm font-semibold">{step.title}</p><p className="mt-1 text-xs leading-5 text-slate-300">{step.copy}</p></div></div>{i < 2 ? <ArrowDown className="my-2 ml-1 h-3 w-3 text-slate-500" /> : null}</div>)}
            </div>
            <p className="border-t border-white/15 pt-5 text-xs leading-6 text-slate-300">Research prototype. Predictions may miss fractures or highlight normal anatomy. Clinical decisions require qualified assessment.</p>
          </div>
        </section>
        <section className="flex items-center">
          <Card className="w-full border-border/80 shadow-soft">
            <CardContent className="p-6 sm:p-8">
              <Outlet />
            </CardContent>
          </Card>
        </section>
      </div>
    </main>
  );
}
