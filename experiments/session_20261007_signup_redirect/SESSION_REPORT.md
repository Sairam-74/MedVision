# Signup flow completion — 7 October 2026

## CURRENT SESSION — 7 October 2026: Automatic signup-to-login flow

- Successful real signup now redirects immediately to `/login` after the backend confirms account creation. The normalized account email is filled in and its password remains blank. Failed/duplicate signup stays on the form with an error; no intermediate confirmation button is required.
- Recovery code appears on the login page in a temporary in-memory receipt, never in URL/history state or local/session storage. It can be dismissed after saving and is cleared on successful login or refresh. Personal passwords are never carried through navigation.
- Passed 20 real-browser auth checks (including actual creation, automatic redirect, new-account login, duplicate rejection and password recovery), 9 frontend tests, lint, typecheck and production build. Verified salted account hashes persist in an isolated SQLite database. Evidence: `experiments/session_20261007_signup_redirect/verification.json` and `browser_auth_checks.json`.
- Running demo had prefill disabled; verified its stored credentials and absence of active inference, then restarted only the demo via `Start-Demo.ps1`. Actual demo sign-in with prefill passes at http://localhost:8000/login. Existing account/history, original checkpoint/dataset and protected training sources preserved. Training/queue/watcher untouched. Isolated auth test server stopped after verification.

