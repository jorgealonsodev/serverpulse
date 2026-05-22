/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: '#0e1116',
        card: '#1a1c23',
        border: '#2a2d37',
        accent: '#3b82f6',
        success: '#22c55e',
        danger: '#ef4444',
      },
    },
  },
  plugins: [],
}
