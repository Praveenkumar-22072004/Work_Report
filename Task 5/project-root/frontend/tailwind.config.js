/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",               // Root HTML
    "./src/**/*.{js,ts,jsx,tsx}", // All React components/pages
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#2563eb", // Blue 600
          dark: "#1e40af",   // Blue 800
          light: "#3b82f6",  // Blue 500
        },
        secondary: {
          DEFAULT: "#9333ea", // Purple 600
          dark: "#7e22ce",    // Purple 700
          light: "#a855f7",   // Purple 500
        },
        accent: {
          DEFAULT: "#f59e0b", // Amber 500
          dark: "#d97706",    // Amber 600
          light: "#fbbf24",   // Amber 400
        },
        background: "#f9fafb", // Light gray background
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        heading: ["Poppins", "sans-serif"],
      },
      boxShadow: {
        soft: "0 2px 8px rgba(0,0,0,0.08)",
        strong: "0 4px 16px rgba(0,0,0,0.15)",
      },
      borderRadius: {
        xl: "1rem",
        "2xl": "1.5rem",
      },
    },
  },
  plugins: [
    require("@tailwindcss/forms"), // Better default form styles
  ],
}
