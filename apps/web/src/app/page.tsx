import { redirect } from "next/navigation";
import { Logo } from "@/components/logo";
import { buttonVariants } from "@/components/ui/button";
import { getCurrentUser } from "@/lib/auth";

const SIGN_IN_HREF = "/api/v1/auth/google/login";

export default async function LandingPage() {
  if (await getCurrentUser()) redirect("/me");

  return (
    <main className="mx-auto flex min-h-dvh max-w-6xl flex-col px-6 pb-16">
      <header className="flex items-center justify-between py-6">
        <Logo />
        <a href={SIGN_IN_HREF} className={buttonVariants({ variant: "outline", size: "sm" })}>
          Sign in
        </a>
      </header>

      <section className="grid flex-1 items-center gap-14 py-10 lg:grid-cols-[1.1fr_0.9fr]">
        <div>
          <h1 className="text-5xl font-extrabold leading-[1.02] sm:text-6xl">
            Find the people to build it with.
          </h1>
          <p className="mt-6 max-w-[34rem] text-lg leading-relaxed text-slate">
            Itr8 is where engineering students post what they&apos;re building, say what help
            they need, and find teammates who have it. We&apos;re starting with IIIT Raichur.
          </p>
          <div className="mt-9 flex flex-wrap items-center gap-4">
            <a href={SIGN_IN_HREF} className={buttonVariants({ size: "lg" })}>
              Continue with Google
            </a>
            <p className="text-sm text-slate">Use your IIIT Raichur college account.</p>
          </div>
        </div>

        <aside aria-label="Example of a team request" className="lg:justify-self-end">
          <div className="w-full max-w-md rotate-[1.2deg] rounded-2xl border border-line bg-card p-6 shadow-[0_18px_40px_-24px_rgba(16,27,51,0.45)]">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm text-slate">Example project</p>
                <h2 className="mt-1 text-2xl font-bold leading-tight">CCTV weapon detection</h2>
              </div>
              <span className="rounded-md bg-marker px-2.5 py-1 text-sm font-semibold">Open role</span>
            </div>
            <p className="mt-4 text-[15px] leading-relaxed text-slate">
              Real-time detection on camera feeds. The model works — it needs an API and a dashboard.
            </p>
            <dl className="mt-5 space-y-3 border-t border-line pt-5 text-[15px]">
              <div className="flex justify-between gap-6">
                <dt className="text-slate">Looking for</dt>
                <dd className="text-right font-semibold">Backend developer</dd>
              </div>
              <div className="flex justify-between gap-6">
                <dt className="text-slate">Skills</dt>
                <dd className="text-right font-semibold">FastAPI, PostgreSQL</dd>
              </div>
              <div className="flex justify-between gap-6">
                <dt className="text-slate">Time</dt>
                <dd className="text-right font-semibold">5 hours a week for 2 months</dd>
              </div>
            </dl>
          </div>
          <p className="mt-6 max-w-md text-sm text-slate">
            Posting projects and roles like this is coming next. Right now you can set up your builder
            profile.
          </p>
        </aside>
      </section>
    </main>
  );
}
