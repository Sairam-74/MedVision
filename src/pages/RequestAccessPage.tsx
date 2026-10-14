import { useForm } from 'react-hook-form';
import { useState } from 'react';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { Link, useNavigate } from 'react-router-dom';
import { signup, authErrorMessage } from '@/api/auth';
import { useRegistrationReceiptStore } from '@/store/registrationReceiptStore';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useMockMode } from '@/utils/env';

const schema = z.object({
  name: z.string().min(2, 'Name is required'),
  email: z.string().email('Enter a valid email'),
  password: z.string().min(12, 'Password must be at least 12 characters').max(256),
  confirmPassword: z.string().min(12, 'Confirm your password'),
}).refine((values) => values.password === values.confirmPassword, {
  message: 'Passwords must match',
  path: ['confirmPassword'],
});

type FormValues = z.infer<typeof schema>;

export function RequestAccessPage() {
  const navigate = useNavigate();
  const mockMode = useMockMode();
  const [genericError, setGenericError] = useState<string | null>(null);
  const setReceipt = useRegistrationReceiptStore((state) => state.setReceipt);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { name: '', email: '', password: '', confirmPassword: '' },
  });

  const onSubmit = handleSubmit(async (values) => {
    setGenericError(null);
    useRegistrationReceiptStore.getState().clear();
    try {
      const email = values.email.trim().toLowerCase();
      let recoveryCode: string;
      if (!mockMode) {
        const response = await signup({
          name: values.name,
          email,
          password: values.password,
        });
        recoveryCode = response.recoveryCode;
      } else {
        recoveryCode = 'test-only-recovery-code-not-a-real-account';
      }
      setReceipt({ email, recoveryCode });
      navigate('/login', { replace: true, state: { accountCreated: true, identifier: email } });
    } catch (error) {
      setGenericError(authErrorMessage(error, 'Could not create your account. Please try again.'));
      return;
    }
  });


  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-medium uppercase tracking-[0.24em] text-muted-foreground">Create account</p>
        <h2 className="mt-2 text-2xl font-semibold">Sign up</h2>
        <p className="mt-1 text-sm text-muted-foreground">Create your account to start using MedVision AI.</p>
      </div>
      <form className="space-y-4" onSubmit={onSubmit} noValidate>
        {genericError ? <Alert className="border-amber-200 bg-amber-50 text-amber-950"><AlertDescription>{genericError}</AlertDescription></Alert> : null}
        <div className="space-y-2">
          <Label htmlFor="name">Full name</Label>
          <Input id="name" {...register('name')} />
          {errors.name ? <p className="text-sm text-red-700">{errors.name.message}</p> : null}
        </div>
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input id="email" type="email" autoComplete="email" {...register('email')} />
          {errors.email ? <p className="text-sm text-red-700">{errors.email.message}</p> : null}
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">Password</Label>
          <Input id="password" type="password" autoComplete="new-password" {...register('password')} />
          {errors.password ? <p className="text-sm text-red-700">{errors.password.message}</p> : null}
        </div>
        <div className="space-y-2">
          <Label htmlFor="confirmPassword">Confirm password</Label>
          <Input id="confirmPassword" type="password" autoComplete="new-password" {...register('confirmPassword')} />
          {errors.confirmPassword ? <p className="text-sm text-red-700">{errors.confirmPassword.message}</p> : null}
        </div>
        <Button type="submit" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? 'Creating account…' : 'Sign up'}
        </Button>
        <p className="text-center text-sm text-muted-foreground">
          Already have access?{' '}
          <Link to="/login" className="font-medium text-primary hover:underline">
            Sign in
          </Link>
        </p>
      </form>
    </div>
  );
}
