/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}", "./components/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        // Material You (MD3) purple seed, reusing the existing "brand" token
        // name so every text-brand-*/bg-brand-*/border-brand-* usage across
        // the app re-themes automatically.
        brand: {
          50: "#F7F2FB",
          100: "#EADDFF",
          200: "#D0BCFF",
          500: "#7C6BAE",
          600: "#6750A4",
          700: "#524087",
          accent: "#7D5260",
        },
        // Neutral scale remapped to MD3's warm neutral-variant tones instead
        // of Tailwind's default cool slate, so text-slate-*/bg-slate-*/
        // border-slate-* usage across the app also re-themes automatically.
        slate: {
          50: "#F7F2FA",
          100: "#F3EDF7",
          200: "#E7E0EC",
          300: "#CAC4D0",
          400: "#938F99",
          500: "#79747E",
          600: "#605D66",
          700: "#49454F",
          800: "#322F37",
          900: "#1C1B1F",
        },
        md: {
          background: "#FFFBFE",
          primary: "#6750A4",
          "primary-container": "#EADDFF",
          "on-primary-container": "#21005D",
          secondary: "#625B71",
          "secondary-container": "#E8DEF8",
          "on-secondary-container": "#1D192B",
          tertiary: "#7D5260",
          "tertiary-container": "#FFD8E4",
          "surface-container": "#F3EDF7",
          "surface-container-low": "#E7E0EC",
          "surface-container-high": "#ECE6F0",
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
