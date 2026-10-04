import { useMemo, useState } from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { Bell, LogOut, Menu, MoonStar, SunMedium, Upload, History, LayoutDashboard, Users, FileClock, UserCircle2 } from 'lucide-react';
import { useAuthStore } from '@/store/authStore';
import { useUiStore } from '@/store/uiStore';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/utils/cn';

const baseNav = [
  { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { label: 'Upload', href: '/upload', icon: Upload },
  { label: 'History', href: '/history', icon: History },
  { label: 'Profile', href: '/profile', icon: UserCircle2 },
  { label: 'Audit Log', href: '/audit-log', icon: FileClock },
];

export function AppShell() {
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const theme = useUiStore((state) => state.theme);
  const toggleTheme = useUiStore((state) => state.toggleTheme);
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const navItems = useMemo(() => [...baseNav, ...(user?.role === 'admin' ? [{ label: 'User Management', href: '/admin/users', icon: Users }] : [])], [user?.role]);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-30 border-b border-border bg-background/90 backdrop-blur">
        <div className="mx-auto flex max-w-[1600px] items-center justify-between gap-4 px-4 py-3 lg:px-8">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon" className="lg:hidden" aria-label="Open navigation" onClick={() => setMobileNavOpen((value) => !value)}>
              <Menu className="h-5 w-5" />
            </Button>
            <div>
              <p className="text-xs uppercase tracking-[0.25em] text-muted-foreground">MedVision AI</p>
              <h1 className="text-lg font-semibold">Enterprise fracture review</h1>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon" aria-label="Notifications" title="Notifications">
              <Bell className="h-5 w-5" />
            </Button>
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
        <aside className={cn('fixed inset-x-0 top-[57px] z-20 border-b border-border bg-background px-4 py-4 shadow-soft lg:static lg:top-0 lg:z-auto lg:block lg:w-72 lg:border-b-0 lg:border-r lg:px-0 lg:py-6', mobileNavOpen ? 'block' : 'hidden lg:block')}>
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
                    active ? 'bg-primary text-primary-foreground' : 'text-foreground hover:bg-muted',
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
            <p className="text-xs uppercase tracking-[0.25em] text-muted-foreground">Current session</p>
            <p className="mt-2 text-sm text-foreground">{user?.name}</p>
            <p className="text-sm text-muted-foreground">{user?.email}</p>
            <div className="mt-4 flex gap-2">
              <Badge variant="outline">Protected</Badge>
              <Badge variant="outline">Audit enabled</Badge>
            </div>
          </div>
        </aside>
        <main className="flex-1 px-4 py-6 lg:px-8 lg:py-8">
          <Outlet />
        </main>
      </div>
      <div className="fixed bottom-4 right-4 z-30">
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
              <Button variant="outline" onClick={() => {}}>
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={() => {
                  logout();
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
