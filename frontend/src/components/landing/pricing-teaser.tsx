"use client";

import { Container } from "./container";
import { SectionHeading } from "./section-heading";
import { Button, Card, Reveal } from "./ui";

const tiers = [
  { title: "Starter", desc: "For small lounges that want clean session tracking" },
  { title: "Growth", desc: "For busy lounges ready for automation and visibility" },
  { title: "Enterprise / Multi-Branch", desc: "For operators running multiple locations or custom workflows" }
] as const;

export function PricingTeaser() {
  return (
    <section id="pricing" className="py-16 sm:py-20">
      <Container>
        <div className="flex flex-col gap-10 lg:flex-row lg:items-end lg:justify-between">
          <Reveal>
            <SectionHeading
              eyebrow="Pricing"
              title="Simple pricing built for growing lounges"
              description="Choose a plan that fits your lounge today, then scale as you add stations or branches."
            />
          </Reveal>
          <Reveal delay={0.06}>
            <div className="flex items-center gap-3">
              <Button href="#pricing-request" variant="primary">
                Get Pricing
              </Button>
            </div>
          </Reveal>
        </div>

        <div className="mt-10 grid gap-4 lg:grid-cols-3">
          {tiers.map((t, i) => (
            <Reveal key={t.title} delay={i * 0.04}>
              <Card className="p-6">
                <div className="text-lg font-semibold text-arc-text">{t.title}</div>
                <p className="mt-2 text-sm leading-relaxed text-arc-muted">{t.desc}</p>
                <div className="mt-4 h-px w-full bg-white/10" />
                <p className="mt-4 text-sm text-arc-muted">
                  Custom onboarding available for lounges that want ESP32 station automation.
                </p>
              </Card>
            </Reveal>
          ))}
        </div>

        <div id="pricing-request" className="sr-only">
          Request pricing
        </div>
      </Container>
    </section>
  );
}

