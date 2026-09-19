import type { Metadata, Viewport } from "next";
import "@fontsource-variable/bricolage-grotesque";
import "@fontsource-variable/instrument-sans";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "Builder Hub", template: "%s · Builder Hub" },
  description:
    "Find teammates, showcase what you build, and collaborate with other engineering students. Now piloting at IIIT Raichur.",
};

export const viewport: Viewport = { themeColor: "#f4f6fa" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-dvh bg-paper text-ink">{children}</body>
    </html>
  );
}
