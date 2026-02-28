/** @type {import('tailwindcss').Config} */
const defaultTheme = require('tailwindcss/defaultTheme');

module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', ...defaultTheme.fontFamily.sans],
      },
      colors: {
        'deep-night': '#11001C',
        'royal-plum': '#290025',
        'dark-berry': '#35012C',
        'neon-violet': '#4F0147',
        'neon-glow': '#9B30FF',
        'neon-glow-light': '#BF40FF',
        'surface-subtle': '#F9F5FC',
        'text-muted': '#6B5B7B',
      },
      boxShadow: {
        'neon': '0 0 15px rgba(79, 1, 71, 0.3), 0 0 45px rgba(155, 48, 255, 0.1)',
        'neon-lg': '0 0 25px rgba(79, 1, 71, 0.4), 0 0 60px rgba(155, 48, 255, 0.15)',
        'neon-btn': '0 4px 20px rgba(79, 1, 71, 0.35), 0 0 40px rgba(155, 48, 255, 0.12)',
        'card': '0 4px 24px rgba(17, 0, 28, 0.06)',
        'card-hover': '0 8px 40px rgba(17, 0, 28, 0.10), 0 0 20px rgba(79, 1, 71, 0.06)',
      },
      animation: {
        'glow-pulse': 'glow-pulse 3s ease-in-out infinite',
        'float': 'float 6s ease-in-out infinite',
        'fade-in': 'fade-in 0.6s ease-out',
        'slide-up': 'slide-up 0.5s ease-out',
      },
      keyframes: {
        'glow-pulse': {
          '0%, 100%': { opacity: '0.4' },
          '50%': { opacity: '0.8' },
        },
        'float': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        'slide-up': {
          from: { opacity: '0', transform: 'translateY(20px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
