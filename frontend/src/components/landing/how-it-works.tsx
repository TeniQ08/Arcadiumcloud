"use client";

import { Container } from "./container";
import { SectionHeading } from "./section-heading";
import { Card, Reveal } from "./ui";

const steps = [
  {
    title: "Customer wants to play",
    desc: "A staff member selects a station and session plan from the dashboard."
  },
  {
    title: "Payment is requested",
    desc: "The customer receives an M-Pesa STK Push prompt and completes payment."
  },
  {
    title: "Station is activated",
    desc: "Once payment is confirmed, Arcadium can trigger the connected ESP32 device to activate the gaming station."
  },
  {
    title: "Session runs in real time",
    desc: "The dashboard tracks the live session, usage, and station state."
  },
  {
    title: "Session ends automatically",
    desc: "When time is up, Arcadium updates the session and can deactivate the station automatically."
  },
  {
    title: "You get full visibility",
    desc: "Track payments, lounge performance, and operations from one system."
  }
] as const;

export function HowItWorks() {
  return (
    <section id="how-it-works" className="py-16 sm:py-20">
      <Container>
        <Reveal>
          <SectionHeading
            eyebrow="How it works"
            title="How Arcadium works"
            description="Less manual work. Better control. More confidence in your revenue."
          />
        </Reveal>

        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {steps.map((s, i) => (
            <Reveal key={s.title} delay={i * 0.03}>
              <Card className="p-5">
                <div className="flex items-center justify-between">
                  <div className="text-xs font-medium text-arc-muted">Step {i + 1}</div>
                  <span className="h-1.5 w-10 rounded-full bg-gradient-to-r from-arc-primary/70 to-arc-highlight/70" />
                </div>
                <div className="mt-3 text-base font-semibold text-arc-text">{s.title}</div>
                <p className="mt-2 text-sm leading-relaxed text-arc-muted">{s.desc}</p>
              </Card>
            </Reveal>
          ))}
        </div>
      </Container>
    </section>
  );
}

