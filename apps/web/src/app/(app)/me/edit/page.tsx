import type { Metadata } from "next";
import { ProfileForm } from "@/features/profiles/profile-form";
import { requireOnboardedUser } from "@/lib/auth";

export const metadata: Metadata = { title: "Edit profile" };

export default async function EditProfilePage() {
  const user = await requireOnboardedUser();

  return (
    <main className="pb-16">
      <h1 className="text-4xl font-extrabold">Edit profile</h1>
      <div className="mt-8 rounded-2xl border border-line bg-card p-6 sm:p-8">
        <ProfileForm
          initial={{
            name: user.name,
            branch: user.profile.branch ?? "",
            year: String(user.profile.year ?? ""),
            bio: user.profile.bio ?? "",
          }}
        />
      </div>
    </main>
  );
}
