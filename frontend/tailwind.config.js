/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        support: {
          primary: "var(--color-support-primary)",
          "primary-light": "var(--color-support-primary-light)",
          success: "var(--color-support-success)",
          warning: "var(--color-support-warning)",
          danger: "var(--color-support-danger)",
          "danger-bg": "var(--color-support-danger-bg)",
          "danger-text": "var(--color-support-danger-text)",
          text: "var(--color-support-text)",
          "text-muted": "var(--color-support-text-muted)",
          "text-faint": "var(--color-support-text-faint)",
          border: "var(--color-support-border)",
          "border-strong": "var(--color-support-border-strong)",
          surface: "var(--color-support-surface)",
          "surface-alt": "var(--color-support-surface-alt)",
        },
      },
      borderRadius: {
        bubble: "var(--radius-bubble)",
      },
    },
  },
  plugins: [],
};
