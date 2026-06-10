/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx,html}",
  ],
  theme: {
    extend: {
      colors: {
        spaceBg: '#050710',
        electricBlue: '#4fc3f7',
        accentViolet: '#b388ff',
        mintGreen: '#69f0ae',
      },
      fontFamily: {
        space: ['Space Grotesk', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
