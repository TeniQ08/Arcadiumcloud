import type { ReactNode } from "react";

export function SectionHeading({
  eyebrow,
  title,
  description,
  align = "left"
}: {
  eyebrow?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  align?: "left" | "center";
}) {
  const alignCls = align === "center" ? "text-center" : "text-left";
  return (
    <div className={["max-w-2xl", align === "center" ? "mx-auto" : "", alignCls]
      .filter(Boolean)
      .join(" ")}>
      {eyebrow ? (
        <div className="mb-4 inline-flex items-center rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-medium tracking-wide text-arc-muted/95">
          {eyebrow}
        </div>
      ) : null}
      <h2 className="text-balance text-3xl font-semibold leading-tight tracking-tight text-arc-text sm:text-4xl">
        {title}
      </h2>
      {description ? (
        <p className="mt-4 text-pretty text-base leading-relaxed text-arc-muted/95 sm:text-lg">
          {description}
        </p>
      ) : null}
    </div>
  );
}

