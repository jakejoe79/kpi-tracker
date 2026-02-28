/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ['Barlow Condensed', 'sans-serif'],
        sans: ['Inter', 'sans-serif'],
      },
      colors: {
        background: '#09090B',
        surface: '#18181B',
        'surface-highlight': '#27272A',
        primary: {
          DEFAULT: '#F97316',
          glow: 'rgba(249, 115, 22, 0.4)',
        },
        secondary: {
          DEFAULT: '#3B82F6',
        },
        success: '#22C55E',
        border: 'rgba(255, 255, 255, 0.1)',
        'text-primary': '#FAFAFA',
        'text-secondary': '#A1A1AA',
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      boxShadow: {
        'glow-primary': '0 0 30px -10px rgba(249, 115, 22, 0.4)',
        'glow-secondary': '0 0 30px -10px rgba(59, 130, 246, 0.4)',
        'glow-success': '0 0 30px -10px rgba(34, 197, 94, 0.4)',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
}
