import type { Metadata } from "next";
import Link from "next/link";
import { Avatar } from "@/components/avatar";
import { buttonVariants } from "@/components/ui/button";
import { YEARS } from "@/features/profiles/schema";
import { requireOnboardedUser } from "@/lib/auth";

export const metadata: Metadata = { title: "Your profile" };

export default async function MyProfilePage() {
  const user = await requireOnboardedUser();
  const year = YEARS.find((y) => y.value === String(user.profile.year))?.label;

  return (
    <main className="pb-16">
      <div className="rounded-2xl border border-line bg-card p-6 sm:p-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-center gap-4">
            <Avatar name={user.name} src={user.avatar_url} size={64} />
            <div>
              <h1 className="text-3xl font-extrabold leading-tight">{user.name}</h1>
              <p className="text-slate">{user.college.name}</p>
            </div>
          </div>
          <Link href="/me/edit" className={buttonVariants({ variant: "outline", size: "sm" })}>
            Edit profile
          </Link>
        </div>

        <dl className="mt-8 grid gap-6 sm:grid-cols-2">
          <div>
            <dt className="text-sm text-slate">Branch</dt>
            <dd className="mt-1 font-semibold">{user.profile.branch}</dd>
          </div>
          <div>
            <dt className="text-sm text-slate">Year</dt>
            <dd className="mt-1 font-semibold">{year}</dd>
          </div>
          <div className="sm:col-span-2">
            <dt className="text-sm text-slate">Email</dt>
            <dd className="mt-1 font-semibold">{user.email}</dd>
          </div>
          <div className="sm:col-span-2">
            <dt className="text-sm text-slate">Bio</dt>
            <dd className="mt-1 whitespace-pre-line leading-relaxed">
              {user.profile.bio ?? (
                <Link href="/me/edit" className="text-signal underline underline-offset-2">
                  Add a short bio so people know what you like building
                </Link>
              )}
            </dd>
          </div>
        </dl>
      </div>

      <p className="mt-6 text-sm text-slate">
        Next up: skills, projects, and finding teammates. Your profile is ready for them.
      </p>
    </main>
  );
}
