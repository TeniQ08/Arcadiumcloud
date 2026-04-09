"use client";

import { Container } from "./container";
import { SectionHeading } from "./section-heading";
import { Card, Reveal } from "./ui";

const pains = [
  "Manual timing causes mistakes",
  "Staff forget to stop sessions",
  "Payments are hard to track",
  "No real-time control of stations",
  "Revenue leakage hurts growth"
] as const;

export function Problem() {
  return (
    <section className="py-16 sm:py-20">
      <Container>
        <Reveal>
          <SectionHeading
            eyebrow="The problem"
            title="Managing a gaming lounge should not be chaotic"
            description="Most lounges still run on manual timing, verbal tracking, and cash handling. That creates session disputes, missed stop times, messy payments, and quiet revenue loss. Arcadium replaces guesswork with a clear system built for how lounges actually operate."
          />
        </Reveal>

        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {pains.map((p, i) => (
            <Reveal key={p} delay={i * 0.04}>
              <Card className="p-5">
                <div className="text-base font-semibold text-arc-text">{p}</div>
                <p className="mt-2 text-sm leading-relaxed text-arc-muted">
                  When timing and payments aren’t connected, small errors become daily losses.
                </p>
              </Card>
            </Reveal>
          ))}
        </div>
      </Container>
    </section>
  );
}

