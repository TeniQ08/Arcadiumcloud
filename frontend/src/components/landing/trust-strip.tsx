"use client";

import { Container } from "./container";
import { Reveal } from "./ui";

const items = [
  "Built for modern gaming lounges",
  "M-Pesa-ready workflows",
  "Cloud-based operations",
  "Automation-driven control"
] as const;

export function TrustStrip() {
  return (
    <section aria-label="Positioning" className="border-y border-white/10 bg-black/10">
      <Container className="py-5">
        <Reveal>
          <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
            {items.map((t) => (
              <div key={t} className="inline-flex items-center gap-2 text-sm text-arc-muted">
                <span className="h-1.5 w-1.5 rounded-full bg-gradient-to-b from-arc-highlight to-arc-primary" />
                <span className="font-medium">{t}</span>
              </div>
            ))}
          </div>
        </Reveal>
      </Container>
    </section>
  );
}

