import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        base: "#070b14",
        panel: "#111827",
        panelMuted: "#161f30",
        border: "#2c3c58",
        textPrimary: "#e5ecf7",
        textSecondary: "#94a5c4",
        accent: "#3aa3ff",
        danger: "#ff6b6b",
        success: "#2ecc71",
        warning: "#f6c343"
      },
      boxShadow: {
        panel: "0 12px 40px rgba(0, 0, 0, 0.35)"
      }
    }
  },
  plugins: []
};

export default config;
