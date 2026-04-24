/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './apps/**/*.py',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
      },
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          500: '#3b82f6',
          600: '#2563eb', // Azul institucional
          700: '#1d4ed8',
          900: '#1e3a8a',
        },
        secondary: '#64748b',
        accent: '#10b981', // Verde esmeralda para acciones
        background: '#f8fafc',
      }
    },
  },
  plugins: [],
}
