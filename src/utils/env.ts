function readBooleanEnv(value: string | undefined, defaultValue: boolean) {
  if (value === 'true') {
    return true;
  }
  if (value === 'false') {
    return false;
  }
  return defaultValue;
}

export function useMockMode() {
  if (import.meta.env.PROD) return false;
  return readBooleanEnv(import.meta.env.VITE_USE_MOCKS, false);
}

export function useMfaMode() {
  return useMockMode() && readBooleanEnv(import.meta.env.VITE_FEATURE_MFA, false);
}
