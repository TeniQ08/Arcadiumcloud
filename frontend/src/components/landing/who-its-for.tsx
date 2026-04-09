"use client";

import { Container } from "./container";
import { SectionHeading } from "./section-heading";
import { Card, Reveal } from "./ui";

const audiences = [
  "PlayStation gaming lounges",
  "Arcade businesses",
  "Console cafés",
  "Cyber cafés with gaming stations",
  "Multi-branch gaming businesses"
] as const;

export function WhoItsFor() {
  return (
    <section className="py-16 sm:py-20">
      <Container>
        <div className="grid gap-10 lg:grid-cols-2 lg:items-start">
          <Reveal>
            <SectionHeading
              eyebrow="Who it's for"
              title="Built for operators who want more control"
              description="If you charge for gaming time, need better payment tracking, and want tighter station control, Arcadium is built for you."
            />
          </Reveal>

          <div className="grid gap-4 sm:grid-cols-2">
            {audiences.map((a, i) => (
              <Reveal key={a} delay={i * 0.03}>
                <Card className="p-5">
                  <div className="flex items-center gap-3">
                    <span className="h-2 w-2 rounded-full bg-gradient-to-b from-arc-highlight to-arc-primary" />
                    <span className="text-sm font-semibold text-arc-text">{a}</span>
                  </div>
                </Card>
              </Reveal>
            ))}
          </div>
        </div>
      </Container>
    </section>
  );
}

