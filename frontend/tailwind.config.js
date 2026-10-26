/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        bg1: "var(--bg-1)",
        bg2: "var(--bg-2)",
        bg3: "var(--bg-3)",
        glass: "var(--glass)",
        "glass-strong": "var(--glass-strong)",
        "glass-border": "var(--glass-border)",
        ink: "var(--text)",
        "ink-2": "var(--text-2)",
        muted: "var(--text-muted)",
        primary: "var(--primary)",
        secondary: "var(--secondary)",
        success: "var(--success)",
        warning: "var(--warning)",
        danger: "var(--danger)",
      },
      borderRadius: {
        card: "var(--radius-card)",
        control: "var(--radius-control)",
        pill: "var(--radius-pill)",
      },
      boxShadow: {
        glass: "var(--shadow), var(--highlight)",
      },
      fontFamily: {
        sans: ["Inter", "'Noto Sans Bengali'", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
