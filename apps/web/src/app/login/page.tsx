import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { Logo } from "@/components/logo";
import { buttonVariants } from "@/components/ui/button";
import { DevLoginForm } from "@/features/auth/dev-login-form";
import { getCurrentUser } from "@/lib/auth";
import { loginErrorMessage } from "@/lib/login-errors";

export const metadata: Metadata = { title: "Sign in" };

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  if (await getCurrentUser()) redirect("/me");

  const { error } = await searchParams;
  const message = loginErrorMessage(error);
  // Read at request time on the server; the API independently refuses dev login outside local.
  const devLogin = process.env.DEV_LOGIN_ENABLED === "true";

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col px-6 py-6">
      <header className="py-2">
        <Logo />
      </header>
      <section className="flex flex-1 flex-col justify-center pb-20">
        <h1 className="text-4xl font-extrabold">Sign in</h1>
        <p className="mt-3 text-slate">
          Builder Hub is in a pilot for IIIT Raichur students. Sign in with your college Google account.
        </p>

        {message && (
          <p role="alert" className="mt-6 rounded-lg bg-danger-soft px-4 py-3 text-[15px] text-danger">
            {message}
          </p>
        )}

        <a href="/api/v1/auth/google/login" className={buttonVariants({ size: "lg", className: "mt-8 w-full" })}>
          Continue with Google
        </a>

        {devLogin && <DevLoginForm />}
      </section>
    </main>
  );
}
