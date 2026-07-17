/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: {
          light: '#f0f2f5',
          dark: '#000000',
        },
        surface: {
          light: '#ffffff',
          dark: '#0a0a0c', // slightly off-black for surfaces if needed
        },
        primary: {
          light: '#6366f1', // indigo-500
          dark: '#818cf8', // indigo-400
        },
        secondary: {
          light: '#8b5cf6', // violet-500
          dark: '#a78bfa', // violet-400
        },
      },
      boxShadow: {
        'neumorph-light': '8px 8px 16px #d1d5db, -8px -8px 16px #ffffff',
        'neumorph-light-inset': 'inset 8px 8px 16px #d1d5db, inset -8px -8px 16px #ffffff',
        'neumorph-dark': '8px 8px 16px #000000, -8px -8px 16px #1a1a24',
        'neumorph-dark-inset': 'inset 8px 8px 16px #000000, inset -8px -8px 16px #1a1a24',
        'soft': '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
        'soft-dark': '0 10px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5)',
      }
    },
  },
  plugins: [],
}
