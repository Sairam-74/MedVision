import { useMemo } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { useSearchParams, Link } from 'react-router-dom';
import { resetPassword } from '@/api/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { useMockMode } from '@/utils/env';

const schema = z
  .object({
    password: z.string().min(12, 'Password must be at least 12 characters'),
    confirmPassword: z.string().min(12, 'Confirm your password'),
  })
  .refine((values) => values.password === values.confirmPassword, {
    message: 'Passwords must match',
    path: ['confirmPassword'],
  });

type FormValues = z.infer<typeof schema>;

function strengthScore(password: string) {
  const checks = [password.length >= 12, /[A-Z]/.test(password), /[a-z]/.test(password), /\d/.test(password), /[^A-Za-z0-9]/.test(password)];
  return checks.filter(Boolean).length * 20;
}

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || 'demo-token';
  const mockMode = useMockMode();
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting, isSubmitSuccessful },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { password: '', confirmPassword: '' },
  });
  const password = watch('password');
  const score = useMemo(() => strengthScore(password || ''), [password]);

  const onSubmit = handleSubmit(async (values) => {
    if (!mockMode) {
      await resetPassword({ token, password: values.password });
    }
  });

  if (isSubmitSuccessful) {
    return (
      <div className="space-y-4">
        <p className="text-sm uppercase tracking-[0.24em] text-muted-foreground">Reset complete</p>
        <h2 className="text-2xl font-semibold">Password updated</h2>
        <p className="text-sm text-muted-foreground">You can now sign in with your new password.</p>
        <Link to="/login" className="inline-flex text-sm font-medium text-primary hover:underline">
          Return to sign in
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-medium uppercase tracking-[0.24em] text-muted-foreground">Reset password</p>
        <h2 className="mt-2 text-2xl font-semibold">Choose a new password</h2>
        <p className="mt-1 text-sm text-muted-foreground">Use at least 12 characters with upper, lower, number, and symbol.</p>
      </div>
      <form className="space-y-4" onSubmit={onSubmit} noValidate>
        <div className="space-y-2">
          <Label htmlFor="password">New password</Label>
          <Input id="password" type="password" autoComplete="new-password" {...register('password')} />
          <Progress value={score} />
          <ul className="space-y-1 text-sm text-muted-foreground">
            <li>At least 12 characters</li>
            <li>Uppercase and lowercase letters</li>
            <li>At least one number and one symbol</li>
          </ul>
          {errors.password ? <p className="text-sm text-red-700">{errors.password.message}</p> : null}
        </div>
        <div className="space-y-2">
          <Label htmlFor="confirmPassword">Confirm password</Label>
          <Input id="confirmPassword" type="password" autoComplete="new-password" {...register('confirmPassword')} />
          {errors.confirmPassword ? <p className="text-sm text-red-700">{errors.confirmPassword.message}</p> : null}
        </div>
        <Button type="submit" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? 'Updating…' : 'Reset password'}
        </Button>
      </form>
    </div>
  );
}
