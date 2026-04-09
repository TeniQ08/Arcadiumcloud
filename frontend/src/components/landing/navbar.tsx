"use client";

import { useEffect, useMemo, useState } from "react";
import { Container } from "./container";
import { Button } from "./ui";

const nav = [
  { label: "Features", href: "#features" },
  { label: "How It Works", href: "#how-it-works" },
  { label: "Pricing", href: "#pricing" },
  { label: "Testimonials", href: "#testimonials" }
] as const;

export function Navbar() {
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const links = useMemo(() => nav, []);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  return (
    <header
      className={[
        "sticky top-0 z-50 border-b backdrop-blur supports-[backdrop-filter]:bg-black/10",
        scrolled ? "border-white/10 bg-[#0B1020]/70" : "border-transparent bg-transparent"
      ].join(" ")}
    >
      <Container className="py-4">
        <div className="flex items-center justify-between">
          <a href="#" className="group inline-flex items-center gap-2">
            <span className="inline-flex h-9 w-9 items-center justify-center rounded-2xl border border-white/10 bg-white/5 shadow-glow">
              <span className="h-2.5 w-2.5 rounded-full bg-gradient-to-b from-arc-highlight to-arc-primary" />
            </span>
            <span className="text-sm font-semibold tracking-tight text-arc-text">
              Arcadium
            </span>
          </a>

          <nav className="hidden items-center gap-7 md:flex" aria-label="Primary">
            {links.map((l) => (
              <a
                key={l.href}
                href={l.href}
                className="text-sm font-medium text-arc-muted transition hover:text-arc-text"
              >
                {l.label}
              </a>
            ))}
          </nav>

          <div className="hidden items-center gap-3 md:flex">
            <Button href="#demo" variant="primary">
              Book a Demo
            </Button>
          </div>

          <button
            type="button"
            className="inline-flex items-center justify-center rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-sm font-semibold text-arc-text transition hover:bg-white/10 md:hidden"
            aria-label="Open menu"
            aria-expanded={open}
            onClick={() => setOpen((v) => !v)}
          >
            <span className="sr-only">Menu</span>
            <span className="block h-0.5 w-5 bg-arc-text" />
            <span className="ml-2 block h-0.5 w-3 bg-arc-text" />
          </button>
        </div>

        {open ? (
          <div className="md:hidden">
            <div className="mt-4 rounded-2xl border border-white/10 bg-[#121A2B]/70 p-3 shadow-glow">
              <div className="flex flex-col">
                {links.map((l) => (
                  <a
                    key={l.href}
                    href={l.href}
                    className="rounded-xl px-3 py-2 text-sm font-medium text-arc-muted hover:bg-white/5 hover:text-arc-text"
                    onClick={() => setOpen(false)}
                  >
                    {l.label}
                  </a>
                ))}
                <div className="mt-3 px-2">
                  <Button href="#demo" variant="primary">
                    Book a Demo
                  </Button>
                </div>
              </div>
            </div>
          </div>
        ) : null}
      </Container>
    </header>
  );
}

