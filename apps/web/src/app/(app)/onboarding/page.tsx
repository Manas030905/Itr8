import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { ProfileForm } from "@/features/profiles/profile-form";
import { requireUser } from "@/lib/auth";

export const metadata: Metadata = { title: "Set up your profile" };

export default async function OnboardingPage() {
  const user = await requireUser();
  if (user.onboarding_completed) redirect("/me");

  return (
    <main className="pb-16">
      <h1 className="text-4xl font-extrabold">Set up your profile</h1>
      <p className="mt-3 max-w-xl text-slate">
        A few details so other builders know who you are. You can change them any time.
      </p>
      <div className="mt-8 rounded-2xl border border-line bg-card p-6 sm:p-8">
        <ProfileForm
          initial={{
            name: user.name,
            branch: user.profile.branch ?? "",
            year: user.profile.year ? String(user.profile.year) : "",
            bio: user.profile.bio ?? "",
          }}
        />
      </div>
    </main>
  );
}
