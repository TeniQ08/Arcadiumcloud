import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Arcadium — Cloud management for modern gaming lounges",
  description:
    "Arcadium is a cloud-based gaming lounge management system that automates prepaid sessions, M-Pesa payments, real-time station control, and lounge operations from one dashboard."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-dvh bg-[radial-gradient(900px_520px_at_10%_8%,rgba(59,130,246,0.20),transparent_55%),radial-gradient(900px_520px_at_92%_12%,rgba(139,92,246,0.16),transparent_56%),radial-gradient(900px_640px_at_50%_112%,rgba(34,211,238,0.11),transparent_60%),linear-gradient(to_bottom,#0B1020,#060814)]">
        <div className="relative">
          <div className="pointer-events-none absolute inset-0 opacity-[0.06] [background-image:linear-gradient(to_right,rgba(148,163,184,0.18)_1px,transparent_1px),linear-gradient(to_bottom,rgba(148,163,184,0.18)_1px,transparent_1px)] [background-size:56px_56px]" />
          {children}
        </div>
      </body>
    </html>
  );
}

