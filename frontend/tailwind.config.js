/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/app/**/*.{ts,tsx}',
    './src/components/**/*.{ts,tsx}',
    './src/lib/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        'bg-base': '#0A0F1E',
        'bg-card': '#111827',
        'bg-elevated': '#1F2937',
        'accent-blue': '#3B82F6',
        'success': '#10B981',
        'warning': '#F59E0B',
        'critical': '#EF4444',
        'escalate': '#F97316',
        'text-primary': '#F9FAFB',
        'text-muted': '#9CA3AF'
      },
      boxShadow: {
        'soft': '0 10px 30px rgba(0,0,0,0.25)'
      }
    },
  },
  plugins: [],
};
