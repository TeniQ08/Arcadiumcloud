"use client";

import { Container } from "./container";
import { SectionHeading } from "./section-heading";
import { Card, Reveal } from "./ui";

const benefits = [
  {
    title: "Reduce revenue leakage",
    desc: "Every session and payment is tracked more clearly."
  },
  {
    title: "Improve staff accountability",
    desc: "Give your team a structured workflow instead of informal processes."
  },
  {
    title: "Deliver a more professional customer experience",
    desc: "Fast payments and organized sessions make your lounge feel modern."
  },
  {
    title: "Get ready to scale",
    desc: "Operate like a serious gaming business, not just a room with consoles."
  }
] as const;

export function Benefits() {
  return (
    <section className="py-16 sm:py-20">
      <Container>
        <Reveal>
          <SectionHeading
            eyebrow="Outcomes"
            title="Why lounge owners choose Arcadium"
            description="Built to keep operations consistent, payments visible, and station control professional."
          />
        </Reveal>

        <div className="mt-10 grid gap-4 sm:grid-cols-2">
          {benefits.map((b, i) => (
            <Reveal key={b.title} delay={i * 0.04}>
              <Card className="p-6">
                <div className="text-lg font-semibold text-arc-text">{b.title}</div>
                <p className="mt-2 text-sm leading-relaxed text-arc-muted">{b.desc}</p>
              </Card>
            </Reveal>
          ))}
        </div>
      </Container>
    </section>
  );
}

