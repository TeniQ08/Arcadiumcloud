"use client";

import { Container } from "./container";
import { SectionHeading } from "./section-heading";
import { Card, IconBadge, Reveal, SimpleIcon } from "./ui";

const features = [
  {
    title: "Prepaid gaming sessions",
    desc: "Let customers pay before play (including M-Pesa STK Push) so sessions start clean and disputes drop.",
    icon: "credit",
    tone: "cyan"
  },
  {
    title: "Automated station control",
    desc: "Connect ESP32 devices to automatically activate or deactivate stations based on session status.",
    icon: "bolt",
    tone: "blue"
  },
  {
    title: "Real-time lounge dashboard",
    desc: "See which stations are available, in session, awaiting payment, or ending soon—at a glance.",
    icon: "dashboard",
    tone: "violet"
  },
  {
    title: "Accurate session tracking",
    desc: "Track start time, end time, duration, and status without manual timers or memory.",
    icon: "clock",
    tone: "blue"
  },
  {
    title: "Payment visibility",
    desc: "Keep payments, sessions, and activity clearly recorded for daily control and reporting.",
    icon: "credit",
    tone: "cyan"
  },
  {
    title: "Staff-friendly workflow",
    desc: "Clear workflows for admins and attendants—so the team works faster with fewer mistakes.",
    icon: "users",
    tone: "violet"
  },
  {
    title: "Cloud access",
    desc: "Check your lounge anytime—without being on-site.",
    icon: "cloud",
    tone: "cyan"
  },
  {
    title: "Built to scale",
    desc: "Run one lounge today and grow to multiple branches when you’re ready.",
    icon: "scale",
    tone: "blue"
  }
] as const;

export function Features() {
  return (
    <section id="features" className="py-16 sm:py-20">
      <Container>
        <Reveal>
          <SectionHeading
            eyebrow="Features"
            title="Everything you need to run a smarter gaming lounge"
            description="One system for sessions, payments, and control—built for how lounges work."
          />
        </Reveal>

        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {features.map((f, i) => (
            <Reveal key={f.title} delay={i * 0.03}>
              <Card className="h-full p-5">
                <div className="flex items-start gap-4">
                  <IconBadge
                    tone={f.tone as any}
                    icon={<SimpleIcon name={f.icon} />}
                  />
                  <div>
                    <div className="text-base font-semibold text-arc-text">
                      {f.title}
                    </div>
                    <p className="mt-1 text-sm leading-relaxed text-arc-muted">
                      {f.desc}
                    </p>
                  </div>
                </div>
              </Card>
            </Reveal>
          ))}
        </div>
      </Container>
    </section>
  );
}

