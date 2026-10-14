import { useEffect, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Eye, EyeOff } from 'lucide-react';
import { login, fetchDemoCredentials, authErrorMessage } from '@/api/auth';
import { useAuthStore } from '@/store/authStore';
import { useRegistrationReceiptStore } from '@/store/registrationReceiptStore';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { mockSession } from '@/mocks/data';
import { useMfaMode, useMockMode } from '@/utils/env';

const schema = z.object({
  identifier: z.string().min(1, 'Email is required'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  otp: z.string().optional(),
});

type LoginFormValues = z.infer<typeof schema>;
type LoginLocationState = {
  accountCreated?: boolean;
  identifier?: string;
  passwordReset?: boolean;
  from?: { pathname?: string };
} | null;

export function LoginPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const location = useLocation();
  const locationState = location.state as LoginLocationState;
  const receipt = useRegistrationReceiptStore((state) => state.receipt);
  const clearReceipt = useRegistrationReceiptStore((state) => state.clear);
  const loginSession = useAuthStore((state) => state.login);
  const [showPassword, setShowPassword] = useState(false);
  const [genericError, setGenericError] = useState<string | null>(null);
  const [demoFilled, setDemoFilled] = useState(false);
  const [loadingDemo, setLoadingDemo] = useState(false);
  const mfaEnabled = useMfaMode();
  const mockMode = useMockMode();
  const {
    register,
    handleSubmit,
    setValue,
    getFieldState,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      identifier: locationState?.identifier ?? 'demo.clinician@example.invalid',
      password: mockMode && !locationState?.accountCreated ? 'password123' : '',
      otp: '',
    },
  });
  useEffect(() => {
    if (mockMode || locationState?.accountCreated || locationState?.passwordReset || (locationState?.identifier && locationState.identifier !== 'demo.clinician@example.invalid')) return;
    let active = true;
    setLoadingDemo(true);
    fetchDemoCredentials().then(data => {
      if (active && data.enabled && data.email && data.password && !getFieldState('identifier').isDirty && !getFieldState('password').isDirty) {
        setValue('identifier', data.email);
        setValue('password', data.password);
        setDemoFilled(true);
      }
    }).catch(() => {}).finally(() => { if (active) setLoadingDemo(false); });
    return () => { active = false; };
  }, [mockMode, locationState?.accountCreated, locationState?.passwordReset, locationState?.identifier, setValue, getFieldState]);
  const redirectPath = locationState?.from?.pathname ?? '/dashboard';

  const onSubmit = handleSubmit(async (values) => {
    setGenericError(null);
    try {
      const session = mockMode ? mockSession : await login(values);
      clearReceipt();
      queryClient.clear();
      loginSession(session);
      navigate(redirectPath, { replace: true });
    } catch (error) {
      setGenericError(authErrorMessage(error, 'Sign-in failed. Check your email and password.'));
    }
  });

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-medium uppercase tracking-[0.24em] text-muted-foreground">Local demo sign-in</p>
        <h2 className="mt-2 text-2xl font-semibold">Welcome back</h2>
        <p className="mt-1 text-sm text-muted-foreground">{demoFilled ? 'Local demo credentials are filled in. Click Sign in, or enter your own account.' : 'Sign in to your account, or create a new research account.'}</p>
      </div>
      {locationState?.accountCreated ? (
        <Alert className="border-emerald-200 bg-emerald-50 text-emerald-950">
          <AlertDescription>Account created. Sign in with the email and password you just used.</AlertDescription>
        </Alert>
      ) : null}
      {locationState?.accountCreated && receipt && receipt.email === locationState.identifier ? (
        <section className="space-y-3 rounded-lg border border-border bg-muted p-4" aria-label="Account recovery">
          <p className="text-sm leading-6">Save your recovery code somewhere private before signing in. You will need it if you forget your password. This local app does not send recovery emails; this code disappears when you sign in or refresh.</p>
          <p aria-label="Recovery code" className="break-all font-mono text-sm select-all">{receipt.recoveryCode}</p>
          <Button type="button" variant="outline" onClick={clearReceipt}>I saved my recovery code</Button>
        </section>
      ) : null}
      {genericError ? (
        <Alert className="border-red-200 bg-red-50 text-red-950">
          <AlertDescription>{genericError}</AlertDescription>
        </Alert>
      ) : null}
      <form className="space-y-4" onSubmit={onSubmit} noValidate>
        <div className="space-y-2">
          <Label htmlFor="identifier">Email</Label>
          <Input id="identifier" type="email" autoComplete="username" {...register('identifier')} aria-invalid={Boolean(errors.identifier)} />
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
          <Button type="submit" className="w-full" disabled={isSubmitting || loadingDemo}>
            {isSubmitting ? 'Signing in…' : loadingDemo ? 'Preparing demo…' : 'Sign in'}
          </Button>
          <Button type="button" variant="outline" className="w-full" asChild>
            <Link to="/signup">Sign up</Link>
          </Button>
        </div>
      </form>
    </div>
  );
}
