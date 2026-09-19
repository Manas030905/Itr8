import { cache } from "react";
import { redirect } from "next/navigation";
import { serverApi } from "@/lib/api/server";
import type { Me } from "@/lib/api/types";

/** The signed-in user, or null. Deduplicated per request. */
export const getCurrentUser = cache(async (): Promise<Me | null> => {
  const api = await serverApi();
  const { data, response } = await api.GET("/api/v1/auth/me");
  if (response.status === 401) return null;
  if (!data) throw new Error(`Could not load your session (API returned ${response.status})`);
  return data;
});

/** Guard: signed-in users only. */
export async function requireUser(): Promise<Me> {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  return user;
}

/** Guard: signed in AND onboarding finished; otherwise send to onboarding. */
export async function requireOnboardedUser(): Promise<Me> {
  const user = await requireUser();
  if (!user.onboarding_completed) redirect("/onboarding");
  return user;
}
