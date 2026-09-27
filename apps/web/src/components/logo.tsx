import Link from "next/link";

export function Logo() {
  return (
    <Link href="/" className="inline-flex items-center gap-2.5 rounded-md">
      <span aria-hidden="true" className="grid h-6 w-6 grid-cols-2 gap-[3px]">
        <span className="rounded-[3px] bg-ink" />
        <span className="rounded-[3px] bg-marker" />
        <span className="rounded-[3px] bg-ink" />
        <span className="rounded-[3px] bg-ink" />
      </span>
      <span className="font-display text-lg font-bold tracking-tight">Itr8</span>
    </Link>
  );
}
