import { useLayoutEffect, useRef, useState } from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { LogOut, Menu, MoonStar, SunMedium, Upload, History, LayoutDashboard, UserCircle2, FlaskConical, ScanLine, ArrowUpRight } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { logoutSession } from '@/api/auth';
import { useAuthStore } from '@/store/authStore';
import { useUiStore } from '@/store/uiStore';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Dialog, DialogClose, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/utils/cn';

const baseNav = [
  { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { label: 'Upload', href: '/upload', icon: Upload },
  { label: 'History', href: '/history', icon: History },
  { label: 'Research', href: '/research', icon: FlaskConical },
  { label: 'Profile', href: '/profile', icon: UserCircle2 },
];

export function AppShell() {
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const theme = useUiStore((state) => state.theme);
  const toggleTheme = useUiStore((state) => state.toggleTheme);
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const [logoutError, setLogoutError] = useState<string | null>(null);
  const headerRef = useRef<HTMLElement>(null);
  const [headerHeight, setHeaderHeight] = useState(97);
  useLayoutEffect(() => {
    const sync = () => setHeaderHeight(headerRef.current?.getBoundingClientRect().height || 97);
    sync();
    window.addEventListener('resize', sync);
    return () => window.removeEventListener('resize', sync);
  }, []);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const navItems = baseNav;

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header ref={headerRef} className="sticky top-0 z-30 border-b border-border bg-background/90 backdrop-blur">
        <div className="mx-auto flex max-w-[1600px] items-center justify-between gap-4 px-4 py-3 lg:px-8">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon" className="lg:hidden" aria-label="Open navigation" onClick={() => setMobileNavOpen((value) => !value)}>
              <Menu className="h-5 w-5" />
            </Button>
            <div className="hidden rounded-xl bg-primary p-2.5 text-primary-foreground sm:block"><ScanLine className="h-6 w-6" /></div>
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.25em] text-primary">MedVision AI</p>
              <h1 className="text-base font-semibold sm:text-lg">Fracture segmentation workspace</h1>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon" aria-label="Toggle theme" onClick={toggleTheme}>
              {theme === 'light' ? <MoonStar className="h-5 w-5" /> : <SunMedium className="h-5 w-5" />}
            </Button>
            <Badge variant="outline" className="hidden rounded-full px-3 py-1 text-xs sm:inline-flex">
              {user?.organization}
            </Badge>
            <Badge variant="secondary" className="rounded-full px-3 py-1 text-xs capitalize">
              {user?.role}
            </Badge>
          </div>
        </div>
      </header>
      <div className="mx-auto flex max-w-[1600px] gap-0 lg:px-4">
        <aside style={{ top: headerHeight }} className={cn('workspace-sidebar fixed inset-x-0 z-20 border-b px-4 py-4 shadow-soft lg:static lg:z-auto lg:block lg:w-64 lg:shrink-0 lg:border-b-0 lg:border-r lg:px-0 lg:py-6', mobileNavOpen ? 'block' : 'hidden lg:block')}>
          <p className="eyebrow mb-4 hidden px-7 text-slate-400 lg:block">Research workspace</p>
          <nav className="space-y-1 lg:px-4">
            {navItems.map((item) => {
              const active = location.pathname === item.href || location.pathname.startsWith(`${item.href}/`);
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.href}
                  to={item.href}
                  onClick={() => setMobileNavOpen(false)}
                  className={cn(
                    'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
                    active ? 'nav-active' : 'nav-idle',
                  )}
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>
          <Separator className="my-4 hidden lg:block" />
          <div className="hidden px-4 lg:block">
            <p className="eyebrow text-slate-400">Current session</p>
            <p className="mt-2 text-sm font-semibold text-white">{user?.name}</p>
            <p className="mt-1 break-all text-xs text-slate-300">{user?.email}</p>
            <div className="mt-7 rounded-xl border border-slate-600 bg-slate-800/60 p-4">
              <FlaskConical className="mb-3 h-5 w-5 text-cyan-300" />
              <p className="text-sm font-semibold text-white">Evidence before claims</p>
              <p className="mt-2 text-xs leading-5 text-slate-300">Follow training, inspect validation results and understand what the model can establish.</p>
              <NavLink to="/research" onClick={() => setMobileNavOpen(false)} className="mt-3 flex items-center gap-2 text-xs font-semibold text-cyan-200">Explore research <ArrowUpRight className="h-3 w-3" /></NavLink>
            </div>
            <p className="mt-5 text-xs leading-5 text-slate-400">Local research prototype<br />De-identified images only</p>
          </div>
        </aside>
        <main className="min-w-0 flex-1 px-4 py-6 lg:px-8 lg:py-8">
          <Outlet />
        </main>
      </div>
      <div className="mx-auto flex max-w-[1600px] justify-end px-4 pb-4">
        <Dialog>
          <DialogTrigger asChild>
            <Button variant="outline" className="shadow-soft">
              <LogOut className="h-4 w-4" />
              Logout
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Confirm logout</DialogTitle>
              <DialogDescription>You will need to sign in again to continue working in MedVision AI.</DialogDescription>
            </DialogHeader>
            <div className="flex justify-end gap-3">
              <DialogClose asChild><Button variant="outline">
                Cancel
              </Button></DialogClose>
              {logoutError ? <p role="alert">{logoutError}</p> : null}
              <Button
                variant="destructive"
                onClick={async () => {
                  try { await logoutSession(); }
                  catch { setLogoutError('Could not sign out. Check your connection and retry.'); return; }
                  logout();
                  queryClient.clear();
                  navigate('/login', { replace: true });
                }}
              >
                Log out
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>
      {mobileNavOpen ? <div className="fixed inset-0 z-10 bg-slate-950/20 lg:hidden" onClick={() => setMobileNavOpen(false)} aria-hidden="true" /> : null}
    </div>
  );
}
