import { Outlet } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export function AuthShell() {
  return (
    <main className="min-h-screen px-4 py-10 lg:px-8">
      <div className="mx-auto grid min-h-[calc(100vh-5rem)] max-w-7xl gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <section className="rounded-3xl border border-border bg-slate-950 p-8 text-slate-50 shadow-soft lg:p-12">
          <div className="max-w-xl space-y-6">
            <p className="text-sm uppercase tracking-[0.3em] text-slate-300">MedVision AI</p>
            <h1 className="text-4xl font-semibold leading-tight lg:text-5xl">Clinical fracture review workspace for internal imaging teams.</h1>
            <p className="text-base leading-7 text-slate-300">
              Built for technicians and clinicians working with sensitive medical images, audit requirements, and approval workflows.
            </p>
            <div className="grid gap-3 text-sm text-slate-200 sm:grid-cols-2">
              <Card className="border-white/10 bg-white/5 text-slate-50 shadow-none">
                <CardHeader>
                  <CardTitle className="text-base">Secure sessions</CardTitle>
                  <CardDescription className="text-slate-300">Protected routes, silent refresh, and no token persistence in localStorage.</CardDescription>
                </CardHeader>
              </Card>
              <Card className="border-white/10 bg-white/5 text-slate-50 shadow-none">
                <CardHeader>
                  <CardTitle className="text-base">Audit-ready</CardTitle>
                  <CardDescription className="text-slate-300">View, approval, and upload actions are captured for review.</CardDescription>
                </CardHeader>
              </Card>
            </div>
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
