import type { Config } from "tailwindcss";

export default {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        arc: {
          bg: "#0B1020",
          bg2: "#121A2B",
          primary: "#3B82F6",
          secondary: "#8B5CF6",
          highlight: "#22D3EE",
          success: "#22C55E",
          text: "#F8FAFC",
          muted: "#A7B3C7"
        }
      },
      borderRadius: {
        "2xl": "1.25rem"
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(148,163,184,0.12), 0 14px 40px rgba(0,0,0,0.38)",
        "glow-sm": "0 0 0 1px rgba(148,163,184,0.10), 0 10px 26px rgba(0,0,0,0.32)"
      }
    }
  },
  plugins: []
} satisfies Config;

