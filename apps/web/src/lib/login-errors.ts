/** Maps the `?error=` code set by the API's OAuth callback to a message users can act on. */
const MESSAGES: Record<string, string> = {
  domain_not_allowed:
    "That Google account isn't on the pilot list. Sign in with your IIIT Raichur college account.",
  email_not_verified: "Google says that email address isn't verified. Verify it, then try again.",
  cancelled: "Sign-in was cancelled. You can try again whenever you're ready.",
  oauth_failed: "Google sign-in didn't complete. Please try again.",
  not_configured: "Sign-in isn't set up on this server yet. Ask the Builder Hub team.",
  account_disabled: "This account has been disabled. Contact the Builder Hub team.",
  account_conflict:
    "This email is already linked to a different Google account. Contact the Builder Hub team.",
};

export function loginErrorMessage(code: string | undefined): string | null {
  if (!code) return null;
  return MESSAGES[code] ?? "Something went wrong signing you in. Please try again.";
}
