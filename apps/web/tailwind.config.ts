import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Evexía Color Palette - Flat colors only
        safe: {
          DEFAULT: '#5A626A',
          light: '#7A828A',
          dark: '#3A424A',
        },
        natural: {
          DEFAULT: '#8BA88B',
          light: '#ABD0AB',
          dark: '#6B886B',
        },
        nurturing: {
          DEFAULT: '#D0B5B3',
          light: '#F0D5D3',
          dark: '#B09593',
        },
        calm: {
          DEFAULT: '#E6E0D7',
          light: '#F6F0E7',
          dark: '#D6D0C7',
        },
      },
      borderRadius: {
        // Force no rounded corners by default
        none: '0',
        DEFAULT: '0',
      },
    },
  },
  plugins: [],
}

export default config
