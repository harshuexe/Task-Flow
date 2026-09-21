import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#17202a",
        canvas: "#f5f3ee",
        coral: "#e86f51",
        sage: "#8ca58d",
        mustard: "#d8a63d",
      },
      fontFamily: {
        sans: ["var(--font-manrope)", "sans-serif"],
        display: ["var(--font-space-grotesk)", "sans-serif"],
      },
      boxShadow: {
        soft: "0 18px 50px rgba(23, 32, 42, 0.10)",
      },
    },
  },
  plugins: [],
};

export default config;