import { Avatar } from "@/components/avatar";
import { Logo } from "@/components/logo";
import { SignOutButton } from "@/features/auth/sign-out-button";
import { requireUser } from "@/lib/auth";

// Authenticated area. Every page under here is guarded on the server before it renders.
export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const user = await requireUser();

  return (
    <div className="mx-auto min-h-dvh max-w-3xl px-6">
      <header className="flex items-center justify-between py-6">
        <Logo />
        <div className="flex items-center gap-3">
          <Avatar name={user.name} src={user.avatar_url} size={32} />
          <span className="hidden text-sm font-semibold sm:inline">{user.name}</span>
          <SignOutButton />
        </div>
      </header>
      {children}
    </div>
  );
}
