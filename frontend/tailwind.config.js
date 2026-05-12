/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'adapt-bg': '#0a0a0f',
        'adapt-card': '#13131a',
        'adapt-border': '#1f1f2e',
        'adapt-2g': '#ef4444',
        'adapt-3g': '#f97316',
        'adapt-4g': '#22c55e',
        'adapt-wifi': '#3b82f6',
      },
    },
  },
  plugins: [],
}