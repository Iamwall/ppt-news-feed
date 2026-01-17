/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        'display': ['Playfair Display', 'Georgia', 'serif'],
        'sans': ['DM Sans', 'system-ui', 'sans-serif'],
        'mono': ['JetBrains Mono', 'monospace'],
      },
      colors: {
        'ink': {
          50: '#f6f7f9',
          100: '#eceef2',
          200: '#d5d9e2',
          300: '#b0b8c9',
          400: '#8592ab',
          500: '#667391',
          600: '#515c78',
          700: '#434b62',
          800: '#3a4153',
          900: '#343947',
          950: '#1e2128',
        },
        'science': {
          50: '#f0fdfb',
          100: '#ccfbf4',
          200: '#99f6ea',
          300: '#5ee9db',
          400: '#2dd4c4',
          500: '#14b8aa',
          600: '#0d948b',
          700: '#0f7670',
          800: '#115e5a',
          900: '#134e4b',
          950: '#042f2e',
        },
        'accent': {
          50: '#fef3f2',
          100: '#fee4e2',
          200: '#fececa',
          300: '#fcaba4',
          400: '#f87a6f',
          500: '#ef5042',
          600: '#dc3324',
          700: '#b9281a',
          800: '#99241a',
          900: '#7f241c',
          950: '#450e09',
        },
      },
    },
  },
  plugins: [],
}
