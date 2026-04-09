"use client";

import type { PropsWithChildren, ReactNode } from "react";
import { motion, useInView } from "framer-motion";
import { useRef } from "react";

export function Button({
  children,
  href,
  variant = "primary"
}: PropsWithChildren<{
  href: string;
  variant?: "primary" | "secondary" | "ghost";
}>) {
  const base =
    "inline-flex items-center justify-center gap-2 rounded-2xl px-5 py-3.5 text-sm font-semibold transition duration-200 will-change-transform focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-arc-highlight/70 focus-visible:ring-offset-2 focus-visible:ring-offset-[#0B1020]";
  const variants: Record<string, string> = {
    primary:
      "relative overflow-hidden bg-gradient-to-b from-arc-primary to-arc-secondary text-white shadow-[0_14px_44px_rgba(59,130,246,0.20)] hover:-translate-y-0.5 hover:shadow-[0_18px_54px_rgba(59,130,246,0.26)] before:absolute before:inset-0 before:bg-[radial-gradient(closest-side,rgba(34,211,238,0.25),transparent_60%)] before:opacity-0 before:transition before:duration-200 hover:before:opacity-100",
    secondary:
      "border border-white/12 bg-white/5 text-arc-text shadow-glow-sm hover:-translate-y-0.5 hover:border-white/18 hover:bg-white/7",
    ghost:
      "text-arc-text hover:bg-white/5 hover:-translate-y-0.5"
  };
  return (
    <a className={[base, variants[variant]].join(" ")} href={href}>
      {children}
    </a>
  );
}

export function Chip({ children }: PropsWithChildren) {
  return (
    <span className="inline-flex items-center rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-medium text-arc-muted/95">
      {children}
    </span>
  );
}

export function Card({
  children,
  className
}: PropsWithChildren<{ className?: string }>) {
  return (
    <div
      className={[
        "rounded-2xl border border-white/10 bg-[linear-gradient(to_bottom,rgba(255,255,255,0.07),rgba(255,255,255,0.025))] shadow-glow backdrop-blur",
        "transition duration-200 hover:-translate-y-0.5 hover:border-white/15",
        className
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {children}
    </div>
  );
}

export function IconBadge({
  icon,
  tone = "blue"
}: {
  icon: ReactNode;
  tone?: "blue" | "violet" | "cyan" | "green";
}) {
  const tones: Record<string, string> = {
    blue: "from-arc-primary/30 to-transparent text-arc-primary",
    violet: "from-arc-secondary/30 to-transparent text-arc-secondary",
    cyan: "from-arc-highlight/30 to-transparent text-arc-highlight",
    green: "from-arc-success/30 to-transparent text-arc-success"
  };
  return (
    <span
      className={[
        "inline-flex h-10 w-10 items-center justify-center rounded-2xl border border-white/10 bg-gradient-to-b",
        tones[tone]
      ].join(" ")}
      aria-hidden="true"
    >
      {icon}
    </span>
  );
}

export function Reveal({
  children,
  delay = 0
}: PropsWithChildren<{ delay?: number }>) {
  const ref = useRef<HTMLDivElement | null>(null);
  const inView = useInView(ref, { margin: "0px 0px -120px 0px", once: true });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 16 }}
      animate={inView ? { opacity: 1, y: 0 } : undefined}
      transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1], delay }}
    >
      {children}
    </motion.div>
  );
}

export function SimpleIcon({ name }: { name: string }) {
  const cls = "h-5 w-5";
  switch (name) {
    case "bolt":
      return (
        <svg viewBox="0 0 24 24" className={cls} fill="none" stroke="currentColor">
          <path
            d="M13 2L3 14h8l-1 8 11-14h-8l0-6z"
            strokeWidth="1.8"
            strokeLinejoin="round"
          />
        </svg>
      );
    case "credit":
      return (
        <svg viewBox="0 0 24 24" className={cls} fill="none" stroke="currentColor">
          <path
            d="M3 7h18v10H3V7z"
            strokeWidth="1.8"
            strokeLinejoin="round"
          />
          <path d="M3 10h18" strokeWidth="1.8" />
          <path d="M7 14h4" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      );
    case "radar":
      return (
        <svg viewBox="0 0 24 24" className={cls} fill="none" stroke="currentColor">
          <path
            d="M12 21a9 9 0 1 0-9-9"
            strokeWidth="1.8"
            strokeLinecap="round"
          />
          <path d="M12 12l6-6" strokeWidth="1.8" strokeLinecap="round" />
          <path d="M12 3v9h9" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      );
    case "dashboard":
      return (
        <svg viewBox="0 0 24 24" className={cls} fill="none" stroke="currentColor">
          <path
            d="M4 13a8 8 0 1 1 16 0"
            strokeWidth="1.8"
            strokeLinecap="round"
          />
          <path d="M12 13l3-3" strokeWidth="1.8" strokeLinecap="round" />
          <path d="M6 20h12" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      );
    case "clock":
      return (
        <svg viewBox="0 0 24 24" className={cls} fill="none" stroke="currentColor">
          <path
            d="M12 21a9 9 0 1 0-9-9 9 9 0 0 0 9 9z"
            strokeWidth="1.8"
          />
          <path d="M12 7v6l4 2" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      );
    case "cloud":
      return (
        <svg viewBox="0 0 24 24" className={cls} fill="none" stroke="currentColor">
          <path
            d="M7 18h10a4 4 0 0 0 0-8 6 6 0 0 0-11.4 2"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      );
    case "users":
      return (
        <svg viewBox="0 0 24 24" className={cls} fill="none" stroke="currentColor">
          <path
            d="M16 11a4 4 0 1 0-8 0"
            strokeWidth="1.8"
            strokeLinecap="round"
          />
          <path
            d="M4 21a8 8 0 0 1 16 0"
            strokeWidth="1.8"
            strokeLinecap="round"
          />
        </svg>
      );
    case "scale":
      return (
        <svg viewBox="0 0 24 24" className={cls} fill="none" stroke="currentColor">
          <path
            d="M12 3v18"
            strokeWidth="1.8"
            strokeLinecap="round"
          />
          <path
            d="M6 7h12"
            strokeWidth="1.8"
            strokeLinecap="round"
          />
          <path
            d="M7 7l-3 6h6l-3-6zM17 7l-3 6h6l-3-6z"
            strokeWidth="1.8"
            strokeLinejoin="round"
          />
        </svg>
      );
    default:
      return (
        <svg viewBox="0 0 24 24" className={cls} fill="none" stroke="currentColor">
          <path d="M4 12h16" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      );
  }
}

