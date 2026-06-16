/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx,html}",
  ],
  theme: {
    extend: {
      colors: {
        spaceBg: '#faf8f5',
        electricBlue: '#1b3a5b',
        accentViolet: '#4a607a',
        mintGreen: '#2f855a',
      },
      fontFamily: {
        space: ['Space Grotesk', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
