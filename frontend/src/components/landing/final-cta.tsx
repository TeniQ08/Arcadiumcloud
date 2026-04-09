"use client";

import { Container } from "./container";
import { Button, Card, Reveal } from "./ui";

export function FinalCTA() {
  return (
    <section id="demo" className="py-16 sm:py-20">
      <Container>
        <Reveal>
          <Card className="relative overflow-hidden p-8 sm:p-10">
            <div className="pointer-events-none absolute -inset-10 bg-[radial-gradient(closest-side,rgba(34,211,238,0.18),transparent_62%),radial-gradient(closest-side,rgba(59,130,246,0.18),transparent_62%),radial-gradient(closest-side,rgba(139,92,246,0.14),transparent_62%)]" />
            <div className="relative">
              <h3 className="text-balance text-3xl font-semibold tracking-tight text-arc-text sm:text-4xl">
                Turn your gaming lounge into a smarter business
              </h3>
              <p className="mt-3 max-w-2xl text-pretty text-base leading-relaxed text-arc-muted sm:text-lg">
                Arcadium keeps sessions, payments, and station control connected—so you run a tighter, more profitable lounge.
              </p>

              <div className="mt-7 flex flex-col gap-3 sm:flex-row sm:items-center">
                <Button href="#demo" variant="primary">
                  Book a Live Demo
                </Button>
                <Button href="https://app.arcadiumcloud.com" variant="secondary">
                  Start Free Trial
                </Button>
              </div>

              <p className="mt-5 text-sm text-arc-muted">
                Built for lounges in Kenya. Ready for operators everywhere.
              </p>
            </div>
          </Card>
        </Reveal>
      </Container>
    </section>
  );
}

