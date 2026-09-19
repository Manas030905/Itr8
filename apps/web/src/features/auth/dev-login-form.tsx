"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { FieldError, Input, Label } from "@/components/ui/field";

/** Local-only sign-in that skips Google. The API refuses it unless ENVIRONMENT=local. */
export function DevLoginForm() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(e: React.SyntheticEvent<HTMLFormElement>) {
    e.preventDefault();
    setPending(true);
    setError(null);
    try {
      const res = await fetch("/api/v1/auth/dev-login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const body = (await res.json().catch(() => ({}))) as { redirect?: string; error?: string };
      if (res.ok && body.redirect) {
        window.location.assign(body.redirect);
        return;
      }
      setError(body.error === "domain_not_allowed" ? "That email isn't allowed by ALLOWED_EMAIL_DOMAINS." : `Dev sign-in failed (${res.status}).`);
    } finally {
      setPending(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="mt-8 rounded-xl border border-dashed border-slate/50 p-4">
      <p className="mb-3 text-sm text-slate">Local development only — skips Google.</p>
      <Label htmlFor="dev-email">Email</Label>
      <Input id="dev-email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="name@an-allowed-domain" aria-describedby="dev-email-error" />
      <FieldError id="dev-email-error">{error}</FieldError>
      <Button type="submit" variant="outline" size="sm" className="mt-3" disabled={pending}>
        {pending ? "Signing in…" : "Dev sign-in"}
      </Button>
    </form>
  );
}
