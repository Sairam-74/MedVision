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
  return readBooleanEnv(import.meta.env.VITE_USE_MOCKS, true);
}

export function useMfaMode() {
  return readBooleanEnv(import.meta.env.VITE_FEATURE_MFA, false);
}