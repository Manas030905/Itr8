"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api/browser";

export function SignOutButton() {
  const router = useRouter();
  const [pending, setPending] = useState(false);

  async function signOut() {
    setPending(true);
    try {
      await api.POST("/api/v1/auth/logout");
    } finally {
      router.replace("/");
      router.refresh(); // drop cached signed-in server components
    }
  }

  return (
    <Button variant="ghost" size="sm" onClick={signOut} disabled={pending}>
      {pending ? "Signing out…" : "Sign out"}
    </Button>
  );
}
