"use client";

import { Container } from "./container";
import { SectionHeading } from "./section-heading";
import { Card, Reveal } from "./ui";

const testimonials = [
  {
    quote:
      "Arcadium gives structure to the entire lounge. Payments, sessions, and control all feel connected instead of manual.",
    name: "James M.",
    role: "Gaming Lounge Owner",
    location: "Nairobi, Kenya"
  },
  {
    quote:
      "The biggest value is visibility. You can immediately see what is active, what is paid, and what needs attention.",
    name: "Kevin O.",
    role: "Arcade Operator",
    location: "Mombasa, Kenya"
  },
  {
    quote:
      "M-Pesa integration makes this feel built for our market, while the automation makes it feel like a serious global product.",
    name: "Brian N.",
    role: "Console Café Manager",
    location: "Kampala, Uganda"
  }
] as const;

export function Testimonials() {
  return (
    <section id="testimonials" className="py-16 sm:py-20">
      <Container>
        <Reveal>
          <SectionHeading
            eyebrow="Testimonials"
            title="What lounge operators would say"
            description="Realistic feedback from operators who care about visibility, accountability, and automation."
          />
        </Reveal>

        <div className="mt-10 grid gap-4 lg:grid-cols-3">
          {testimonials.map((t, i) => (
            <Reveal key={t.name} delay={i * 0.04}>
              <Card className="p-6">
                <div className="text-sm leading-relaxed text-arc-text/90">
                  “{t.quote}”
                </div>
                <div className="mt-5 h-px w-full bg-white/10" />
                <div className="mt-4">
                  <div className="text-sm font-semibold text-arc-text">
                    — {t.name}, <span className="font-medium">{t.role}</span>
                  </div>
                  <div className="mt-1 text-xs text-arc-muted">{t.location}</div>
                </div>
              </Card>
            </Reveal>
          ))}
        </div>
      </Container>
    </section>
  );
}

