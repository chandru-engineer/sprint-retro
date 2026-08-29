/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}", "./components/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        md: {
          background: "#FFFBFE",
          "on-background": "#1C1B1F",
          primary: "#6750A4",
          "on-primary": "#FFFFFF",
          "primary-container": "#EADDFF",
          "on-primary-container": "#21005D",
          secondary: "#625B71",
          "secondary-container": "#E8DEF8",
          "on-secondary-container": "#1D192B",
          tertiary: "#7D5260",
          "tertiary-container": "#FFD8E4",
          "on-tertiary-container": "#31111D",
          surface: "#FFFBFE",
          "surface-container": "#F3EDF7",
          "surface-container-low": "#E7E0EC",
          "surface-container-high": "#ECE6F0",
          "on-surface": "#1C1B1F",
          "on-surface-variant": "#49454F",
          outline: "#79747E",
          border: "#79747E",
        },
      },
      fontFamily: {
        sans: ["Roboto", "ui-sans-serif", "system-ui", "-apple-system", "sans-serif"],
      },
      borderRadius: {
        xs: "8px",
        sm: "12px",
        md: "16px",
        lg: "24px",
        xl: "28px",
        "2xl": "32px",
        "3xl": "48px",
      },
      transitionTimingFunction: {
        emphasized: "cubic-bezier(0.2, 0, 0, 1)",
      },
    },
  },
  plugins: [],
};
