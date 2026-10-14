import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { Link, useNavigate } from 'react-router-dom';
import { sendPasswordReset, authErrorMessage } from '@/api/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useMockMode } from '@/utils/env';

const schema = z.object({
  email: z.string().email('Enter a valid work email'),
  recoveryCode: z.string().min(20, 'Enter the recovery code saved when you signed up').max(128),
});

type FormValues = z.infer<typeof schema>;

export function ForgotPasswordPage() {
  const navigate = useNavigate();
  const [genericError, setGenericError] = useState<string | null>(null);
  const mockMode = useMockMode();
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = handleSubmit(async (values) => {
    setGenericError(null);
    try {
      if (!mockMode) {
        const response = await sendPasswordReset(values);
        navigate(response.resetUrl);
      } else {
        navigate('/reset-password#token=test-only-recovery-token');
      }
    } catch (error) {
      setGenericError(authErrorMessage(error, 'Could not verify account recovery. Please try again.'));
    }
  });

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-medium uppercase tracking-[0.24em] text-muted-foreground">Forgot password</p>
        <h2 className="mt-2 text-2xl font-semibold">Reset access</h2>
        <p className="mt-1 text-sm leading-6 text-muted-foreground">Enter your email and saved recovery code. After verification, you can choose a new password. This local app does not send emails.</p>
      </div>
      <form className="space-y-4" onSubmit={onSubmit} noValidate>
        {genericError ? <Alert className="border-amber-200 bg-amber-50 text-amber-950"><AlertDescription>{genericError}</AlertDescription></Alert> : null}
        <div className="space-y-2">
          <Label htmlFor="email">Work email</Label>
          <Input id="email" type="email" autoComplete="email" {...register('email')} />
          {errors.email ? <p className="text-sm text-red-700">{errors.email.message}</p> : null}
        </div>
        <div className="space-y-2"><Label htmlFor="recoveryCode">Recovery code</Label><Input id="recoveryCode" type="password" autoComplete="off" {...register('recoveryCode')} />{errors.recoveryCode ? <p className="text-sm text-red-700">{errors.recoveryCode.message}</p> : null}</div>
        <p className="text-xs leading-5 text-muted-foreground">For the shared demo account, the owner can find its code in .local_demo/demo_recovery_code.txt. If your own recovery code is lost, ask the local project owner to help restore access.</p>
        <Button type="submit" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? 'Verifying…' : 'Verify recovery code'}
        </Button>
        <p className="text-center text-sm text-muted-foreground">
          Remembered your password?{' '}
          <Link to="/login" className="font-medium text-primary hover:underline">
            Sign in
          </Link>
        </p>
      </form>
    </div>
  );
}
