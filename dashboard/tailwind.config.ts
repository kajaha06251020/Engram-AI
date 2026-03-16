import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        engram: {
          bg: "#0f0f23",
          card: "#1a1a3e",
          border: "#2a2a4e",
          purple: { DEFAULT: "#818cf8", light: "#a78bfa" },
          green: { DEFAULT: "#34d399", light: "#6ee7b7" },
          red: { DEFAULT: "#f87171", light: "#fca5a5" },
          amber: { DEFAULT: "#fbbf24", light: "#fcd34d" },
        },
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
