import { initials } from "@/lib/utils";

/** Google profile photo, falling back to initials. `no-referrer` keeps Google from seeing our URLs. */
export function Avatar({ name, src, size = 36 }: { name: string; src: string | null; size?: number }) {
  const style = { width: size, height: size };
  if (src) {
    // eslint-disable-next-line @next/next/no-img-element -- remote Google avatar, tiny, not worth next/image config
    return <img src={src} alt="" referrerPolicy="no-referrer" style={style} className="rounded-full bg-line object-cover" />;
  }
  return (
    <span
      aria-hidden="true"
      style={{ ...style, fontSize: size * 0.38 }}
      className="inline-flex items-center justify-center rounded-full bg-ink font-semibold text-white"
    >
      {initials(name)}
    </span>
  );
}
