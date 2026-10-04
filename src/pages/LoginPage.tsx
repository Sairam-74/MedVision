import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Eye, EyeOff } from 'lucide-react';
import { login } from '@/api/auth';
import { useAuthStore } from '@/store/authStore';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { mockSession } from '@/mocks/data';
import { useMfaMode, useMockMode } from '@/utils/env';

const schema = z.object({
  identifier: z.string().min(1, 'Email or username is required'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  otp: z.string().optional(),
});

type LoginFormValues = z.infer<typeof schema>;
type LoginLocationState = {
  accountCreated?: boolean;
  identifier?: string;
  from?: { pathname?: string };
} | null;

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const locationState = location.state as LoginLocationState;
  const loginSession = useAuthStore((state) => state.login);
  const [showPassword, setShowPassword] = useState(false);
  const [genericError, setGenericError] = useState<string | null>(null);
  const mfaEnabled = useMfaMode();
  const mockMode = useMockMode();
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      identifier: locationState?.identifier ?? 'demo.clinician@example.invalid',
      password: '',
      otp: '',
    },
  });
  const redirectPath = locationState?.from?.pathname ?? '/dashboard';

  const onSubmit = handleSubmit(async (values) => {
    setGenericError(null);
    try {
      const session = mockMode ? mockSession : await login(values);
      loginSession(session);
      navigate(redirectPath, { replace: true });
    } catch {
      setGenericError(mockMode ? 'Sign-in failed. Refresh and try again.' : 'Sign-in failed. Check your credentials and try again.');
    }
  });

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-medium uppercase tracking-[0.24em] text-muted-foreground">Secure sign-in</p>
        <h2 className="mt-2 text-2xl font-semibold">Welcome back</h2>
        <p className="mt-1 text-sm text-muted-foreground">Use your hospital or clinic credentials to continue.</p>
      </div>
      {locationState?.accountCreated ? (
        <Alert className="border-emerald-200 bg-emerald-50 text-emerald-950">
          <AlertDescription>Account created. Sign in with the email and password you just used.</AlertDescription>
        </Alert>
      ) : null}
      {genericError ? (
        <Alert className="border-red-200 bg-red-50 text-red-950">
          <AlertDescription>{genericError}</AlertDescription>
        </Alert>
      ) : null}
      <form className="space-y-4" onSubmit={onSubmit} noValidate>
        <div className="space-y-2">
          <Label htmlFor="identifier">Email or username</Label>
          <Input id="identifier" autoComplete="username" {...register('identifier')} aria-invalid={Boolean(errors.identifier)} />
          {errors.identifier ? <p className="text-sm text-red-700">{errors.identifier.message}</p> : null}
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">Password</Label>
          <div className="relative">
            <Input id="password" type={showPassword ? 'text' : 'password'} autoComplete="current-password" {...register('password')} aria-invalid={Boolean(errors.password)} className="pr-11" />
            <Button type="button" variant="ghost" size="icon" className="absolute right-1 top-1 h-8 w-8" aria-label={showPassword ? 'Hide password' : 'Show password'} onClick={() => setShowPassword((value) => !value)}>
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </Button>
          </div>
          {errors.password ? <p className="text-sm text-red-700">{errors.password.message}</p> : null}
        </div>
        {mfaEnabled ? (
          <div className="space-y-2">
            <Label htmlFor="otp">One-time passcode</Label>
            <Input id="otp" inputMode="numeric" autoComplete="one-time-code" {...register('otp')} />
            <p className="text-sm text-muted-foreground">MFA is enabled for this environment.</p>
          </div>
        ) : null}
        <div className="flex items-center justify-between text-sm">
          <Link to="/forgot-password" className="font-medium text-primary hover:underline">
            Forgot password?
          </Link>
          <Link to="/signup" className="font-medium text-primary hover:underline">
            Sign up
          </Link>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <Button type="submit" className="w-full" disabled={isSubmitting}>
            {isSubmitting ? 'Signing in…' : 'Sign in'}
          </Button>
          <Button type="button" variant="outline" className="w-full" asChild>
            <Link to="/signup">Sign up</Link>
          </Button>
        </div>
      </form>
    </div>
  );
}
