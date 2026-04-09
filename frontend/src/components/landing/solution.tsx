"use client";

import { Container } from "./container";
import { SectionHeading } from "./section-heading";
import { Card, IconBadge, Reveal, SimpleIcon } from "./ui";

const pillars = [
  {
    title: "Automate operations",
    desc: "Start and stop stations from a verified session—so timing stays consistent, even across shifts.",
    icon: "bolt",
    tone: "blue"
  },
  {
    title: "Collect payments faster",
    desc: "Prepaid-first workflows (including M-Pesa STK Push) keep every session tied to a payment.",
    icon: "credit",
    tone: "cyan"
  },
  {
    title: "Control your lounge in real time",
    desc: "See what’s active, what’s paid, what needs attention—and act from one dashboard.",
    icon: "radar",
    tone: "violet"
  }
] as const;

export function Solution() {
  return (
    <section className="py-16 sm:py-20">
      <Container>
        <div className="grid gap-10 lg:grid-cols-2 lg:items-start">
          <Reveal>
            <SectionHeading
              eyebrow="The solution"
              title="Arcadium brings payments, automation, and station control into one system"
              description="From the moment a customer pays, Arcadium can activate the station, track time automatically, and keep payments and sessions in sync. This is not just a timer—it’s the operating system for your lounge."
            />
          </Reveal>

          <div className="grid gap-4">
            {pillars.map((p, i) => (
              <Reveal key={p.title} delay={i * 0.05}>
                <Card className="p-5">
                  <div className="flex items-start gap-4">
                    <IconBadge
                      tone={p.tone as any}
                      icon={<SimpleIcon name={p.icon} />}
                    />
                    <div>
                      <div className="text-base font-semibold text-arc-text">
                        {p.title}
                      </div>
                      <p className="mt-1 text-sm leading-relaxed text-arc-muted">
                        {p.desc}
                      </p>
                    </div>
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

