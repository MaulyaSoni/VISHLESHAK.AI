import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        // Streamlit Claude-inspired Dark Theme from app.py
        'bg-base': '#0D0F1C',           // Deep midnight
        'bg-surface': '#161B2E',        // Elevated surface
        'bg-elevated': '#1F2638',       // Secondary surface
        
        // Borders
        'border-subtle': '#2D3548',
        
        // Text
        'text-primary': '#F8FAFC',      // High contrast text
        'text-muted': '#94A3B8',        // Muted text
        
        // Accents - from app.py DARK theme
        'accent-blue': '#6366F1',       // Indigo - primary accent
        'accent-cyan': '#06B6D4',       // Cyan - secondary accent
        'accent-green': '#10B981',      // Green - success/tertiary
        'accent-red': '#EF4444',
        'accent-yellow': '#F59E0B',
        
        // Message backgrounds
        'msg-user': '#1E2638',
        'msg-bot': '#1A1F2E',
        'msg-user-border': '#6366F1',
        'msg-bot-border': '#10B981',
        
        // Domain colors
        'domain-finance': {
          primary: '#1A3A5C',
          accent: '#2E86AB',
          badge: '#0D2137',
        },
        'domain-insurance': {
          primary: '#1A4A2E',
          accent: '#2EAB6E',
          badge: '#0D2B1A',
        },
        'domain-general': {
          primary: '#2A1A4A',
          accent: '#7B4EAB',
          badge: '#1A1030',
        },
      },
      borderRadius: {
        'xl': '16px',
        'lg': '12px',
        'md': '8px',
      },
      boxShadow: {
        'card': '0 4px 20px rgba(0,0,0,0.3)',
        'glow': '0 0 30px rgba(99, 102, 241, 0.3)',
        'glow-cyan': '0 0 30px rgba(6, 182, 212, 0.3)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 3s linear infinite',
        'float': 'float 3s ease-in-out infinite',
        'gradient': 'gradient 8s ease infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        gradient: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
      },
      backgroundImage: {
        'gradient-accent': 'linear-gradient(135deg, #6366F1 0%, #06B6D4 50%, #10B981 100%)',
        'gradient-radial': 'radial-gradient(ellipse at center, var(--tw-gradient-stops))',
      },
    },
  },
  plugins: [],
}

export default config
