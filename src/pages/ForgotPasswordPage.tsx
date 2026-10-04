import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { Link } from 'react-router-dom';
import { sendPasswordReset } from '@/api/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useMockMode } from '@/utils/env';

const schema = z.object({
  email: z.string().email('Enter a valid work email'),
});

type FormValues = z.infer<typeof schema>;

export function ForgotPasswordPage() {
  const [submitted, setSubmitted] = useState(false);
  const mockMode = useMockMode();
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = handleSubmit(async (values) => {
    setSubmitted(true);
    if (!mockMode) {
      await sendPasswordReset(values);
    }
  });

  if (submitted) {
    return (
      <div className="space-y-4">
        <p className="text-sm uppercase tracking-[0.24em] text-muted-foreground">Password reset</p>
        <h2 className="text-2xl font-semibold">Check your email</h2>
        <p className="text-sm text-muted-foreground">If an account exists, a reset link will be sent to the address you entered.</p>
        <Link to="/login" className="inline-flex text-sm font-medium text-primary hover:underline">
          Return to sign in
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-medium uppercase tracking-[0.24em] text-muted-foreground">Forgot password</p>
        <h2 className="mt-2 text-2xl font-semibold">Reset access</h2>
        <p className="mt-1 text-sm text-muted-foreground">We will send a reset link to your work email.</p>
      </div>
      <form className="space-y-4" onSubmit={onSubmit} noValidate>
        <div className="space-y-2">
          <Label htmlFor="email">Work email</Label>
          <Input id="email" type="email" autoComplete="email" {...register('email')} />
          {errors.email ? <p className="text-sm text-red-700">{errors.email.message}</p> : null}
        </div>
        <Button type="submit" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? 'Sending…' : 'Send reset link'}
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
