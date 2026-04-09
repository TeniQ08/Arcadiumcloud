"use client";

import { Container } from "./container";

const links = [
  { label: "Features", href: "#features" },
  { label: "How It Works", href: "#how-it-works" },
  { label: "Pricing", href: "#pricing" },
  { label: "Demo", href: "#demo" },
  { label: "Contact", href: "#demo" }
] as const;

const legal = [
  { label: "Terms", href: "#" },
  { label: "Privacy", href: "#" }
] as const;

export function Footer() {
  return (
    <footer className="border-t border-white/10 bg-black/10 py-12">
      <Container>
        <div className="flex flex-col gap-10 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div className="inline-flex items-center gap-2">
              <span className="inline-flex h-9 w-9 items-center justify-center rounded-2xl border border-white/10 bg-white/5 shadow-glow">
                <span className="h-2.5 w-2.5 rounded-full bg-gradient-to-b from-arc-highlight to-arc-primary" />
              </span>
              <div>
                <div className="text-sm font-semibold text-arc-text">Arcadium</div>
                <div className="text-xs text-arc-muted">
                  Cloud management for modern gaming lounges
                </div>
              </div>
            </div>
            <div className="mt-4 text-sm text-arc-muted">
              <span className="text-arc-text/90">arcadiumcloud.com</span>
            </div>
          </div>

          <div className="grid gap-8 sm:grid-cols-2">
            <div>
              <div className="text-xs font-semibold uppercase tracking-wide text-arc-muted">
                Product
              </div>
              <div className="mt-3 flex flex-col gap-2">
                {links.map((l) => (
                  <a
                    key={l.href + l.label}
                    href={l.href}
                    className="text-sm font-medium text-arc-muted transition hover:text-arc-text"
                  >
                    {l.label}
                  </a>
                ))}
              </div>
            </div>
            <div>
              <div className="text-xs font-semibold uppercase tracking-wide text-arc-muted">
                Legal
              </div>
              <div className="mt-3 flex flex-col gap-2">
                {legal.map((l) => (
                  <a
                    key={l.label}
                    href={l.href}
                    className="text-sm font-medium text-arc-muted transition hover:text-arc-text"
                  >
                    {l.label}
                  </a>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="mt-10 h-px w-full bg-white/10" />
        <div className="mt-6 flex flex-col gap-2 text-xs text-arc-muted sm:flex-row sm:items-center sm:justify-between">
          <div>© {new Date().getFullYear()} Arcadium. All rights reserved.</div>
          <div>
            App:{" "}
            <a
              href="https://app.arcadiumcloud.com"
              className="font-medium text-arc-text/90 hover:text-arc-text"
            >
              app.arcadiumcloud.com
            </a>
          </div>
        </div>
      </Container>
    </footer>
  );
}

