module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx,html}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["'Inter'", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "'Fira Code'", "monospace"]
      },
      colors: {
        cl: {
          blue:      "#1565C0",
          "blue-2":  "#1976D2",
          "blue-3":  "#2196F3",
          "blue-4":  "#42A5F5",
          "blue-5":  "#90CAF9",
          cyan:      "#00BCD4",
          "cyan-2":  "#26C6DA",
          "cyan-3":  "#00E5FF",
          dark:      "#0A0E1A",
          "dark-2":  "#0D1421",
          "dark-3":  "#111827",
          "dark-4":  "#1a2234",
          "dark-5":  "#1e2d45",
          glass:     "rgba(13,20,33,0.75)",
        }
      },
      backgroundImage: {
        "circuit": "radial-gradient(circle at 20% 50%, rgba(21,101,192,0.15) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(0,188,212,0.1) 0%, transparent 40%)",
        "glow-blue": "radial-gradient(circle, rgba(33,150,243,0.3) 0%, transparent 70%)",
      },
      boxShadow: {
        "glow-sm":  "0 0 10px rgba(33,150,243,0.3)",
        "glow":     "0 0 20px rgba(33,150,243,0.4)",
        "glow-lg":  "0 0 40px rgba(33,150,243,0.5)",
        "glow-cyan":"0 0 20px rgba(0,229,255,0.4)",
        "card":     "0 4px 24px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.06)",
      },
      animation: {
        "pulse-glow":   "pulse-glow 2s ease-in-out infinite",
        "float":        "float 6s ease-in-out infinite",
        "circuit-on":   "circuit-on 1.5s ease forwards",
        "slide-up":     "slide-up 0.5s ease forwards",
        "fade-in":      "fade-in 0.4s ease forwards",
        "spin-slow":    "spin 8s linear infinite",
        "ping-slow":    "ping 3s cubic-bezier(0,0,0.2,1) infinite",
      },
      keyframes: {
        "pulse-glow": {
          "0%, 100%": { boxShadow: "0 0 10px rgba(33,150,243,0.3)" },
          "50%":      { boxShadow: "0 0 25px rgba(33,150,243,0.7), 0 0 50px rgba(33,150,243,0.2)" }
        },
        "float": {
          "0%, 100%": { transform: "translateY(0)" },
          "50%":      { transform: "translateY(-10px)" }
        },
        "circuit-on": {
          "0%":   { opacity: "0", strokeDashoffset: "100" },
          "100%": { opacity: "1", strokeDashoffset: "0" }
        },
        "slide-up": {
          "0%":   { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" }
        },
        "fade-in": {
          "0%":   { opacity: "0" },
          "100%": { opacity: "1" }
        }
      }
    }
  },
  plugins: []
};
