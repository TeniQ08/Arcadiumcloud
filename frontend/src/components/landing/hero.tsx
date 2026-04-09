"use client";

import { Container } from "./container";
import { Button, Card, Chip, Reveal } from "./ui";

function DashboardMock() {
  const stations = [
    { name: "PS5-01", state: "In session", tone: "bg-arc-success/15 text-arc-success border-arc-success/25" },
    { name: "PS5-02", state: "Available", tone: "bg-white/6 text-arc-muted border-white/10" },
    { name: "PS5-03", state: "Awaiting payment", tone: "bg-arc-highlight/10 text-arc-highlight border-arc-highlight/25" },
    { name: "PS5-04", state: "Ending soon", tone: "bg-arc-secondary/12 text-arc-secondary border-arc-secondary/25" }
  ] as const;

  return (
    <div className="relative">
      <div className="pointer-events-none absolute -inset-6 rounded-[28px] bg-[radial-gradient(closest-side,rgba(59,130,246,0.28),transparent_65%),radial-gradient(closest-side,rgba(139,92,246,0.22),transparent_60%)] blur-2xl" />
      <Card className="relative overflow-hidden p-5 sm:p-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-semibold text-arc-text">Live Lounge Dashboard</div>
            <div className="mt-1 text-xs text-arc-muted">
              Stations, sessions, and payments—tied together
            </div>
          </div>
          <div className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-medium text-arc-muted">
            Real-time
          </div>
        </div>

        <div className="mt-5 grid grid-cols-2 gap-3">
          {stations.map((s) => (
            <div
              key={s.name}
              className="rounded-2xl border border-white/10 bg-[#0B1020]/40 p-3"
            >
              <div className="flex items-center justify-between">
                <div className="text-sm font-semibold text-arc-text">{s.name}</div>
                <span className={["inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium", s.tone].join(" ")}>
                  {s.state}
                </span>
              </div>
              <div className="mt-3 h-2 w-full rounded-full bg-white/5">
                <div className="h-2 rounded-full bg-gradient-to-r from-arc-primary/70 to-arc-highlight/70" style={{ width: s.state === "In session" ? "72%" : s.state === "Ending soon" ? "88%" : "18%" }} />
              </div>
              <div className="mt-2 flex items-center justify-between text-xs text-arc-muted">
                <span>Session</span>
                <span className="text-arc-text/80">
                  {s.state === "In session" ? "00:43" : s.state === "Ending soon" ? "01:52" : "—"}
                </span>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-4 grid grid-cols-3 gap-3">
          <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
            <div className="text-xs text-arc-muted">Today’s revenue</div>
            <div className="mt-1 text-base font-semibold text-arc-text">Tracked</div>
            <div className="mt-1 text-xs text-arc-muted">Payments tied to sessions</div>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
            <div className="text-xs text-arc-muted">Payments</div>
            <div className="mt-1 text-base font-semibold text-arc-text">M-Pesa STK</div>
            <div className="mt-1 text-xs text-arc-muted">Prepaid by default</div>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
            <div className="text-xs text-arc-muted">Automation</div>
            <div className="mt-1 text-base font-semibold text-arc-text">ESP32</div>
            <div className="mt-1 text-xs text-arc-muted">Station control</div>
          </div>
        </div>

        <div className="mt-4 rounded-2xl border border-white/10 bg-[#0B1020]/35 p-3">
          <div className="flex items-center justify-between">
            <div className="text-xs font-medium text-arc-muted">Latest activity</div>
            <div className="text-xs text-arc-muted">Just now</div>
          </div>
          <div className="mt-2 space-y-2">
            <div className="flex items-center justify-between text-sm">
                <span className="text-arc-text/90">PS5-03 payment confirmed</span>
              <span className="text-xs text-arc-success">Paid</span>
            </div>
            <div className="flex items-center justify-between text-sm">
                <span className="text-arc-text/90">PS5-04 session ending soon</span>
              <span className="text-xs text-arc-secondary">2 min</span>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}

export function Hero() {
  return (
    <section className="relative overflow-hidden">
      <Container className="py-14 sm:py-20">
        <div className="grid items-center gap-10 lg:grid-cols-2">
          <Reveal>
            <div>
              <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-medium text-arc-muted">
                <span className="h-2 w-2 rounded-full bg-arc-success" />
                Built for daily lounge operations.
              </div>

              <h1 className="text-balance text-4xl font-semibold tracking-tight text-arc-text sm:text-5xl">
                Run your gaming lounge like a modern business
              </h1>
              <p className="mt-4 text-pretty text-base leading-relaxed text-arc-muted sm:text-lg">
                Arcadium is the operating system for PlayStation gaming lounges—prepaid sessions, M-Pesa payments,
                live station control, and clear session tracking from one dashboard.
              </p>

              <div className="mt-7 flex flex-col gap-3 sm:flex-row sm:items-center">
                <Button href="#demo" variant="primary">
                  Book a Live Demo
                </Button>
                <Button href="#how-it-works" variant="secondary">
                  See How It Works
                </Button>
              </div>

              <p className="mt-3 text-sm text-arc-muted">
                Book a walkthrough of Arcadium in action—see how it fits your lounge workflow.
              </p>

              <div className="mt-7 flex flex-wrap gap-2">
                <Chip>Prepaid sessions via M-Pesa STK Push</Chip>
                <Chip>Real-time station control</Chip>
                <Chip>Session and payment tracking</Chip>
                <Chip>Built for lounges in Kenya and beyond</Chip>
              </div>
            </div>
          </Reveal>

          <Reveal delay={0.08}>
            <div className="lg:justify-self-end">
              <DashboardMock />
            </div>
          </Reveal>
        </div>
      </Container>
    </section>
  );
}

