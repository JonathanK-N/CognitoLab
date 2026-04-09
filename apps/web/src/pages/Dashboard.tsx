import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ProgressBar } from "@cognitolab/ui";

// ── Animated Circuit background ───────────────
const CircuitParticles: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    canvas.width  = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    const nodes: { x: number; y: number; vx: number; vy: number; r: number; pulse: number }[] = [];
    for (let i = 0; i < 20; i++) {
      nodes.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.3,
        r: Math.random() * 2 + 1,
        pulse: Math.random() * Math.PI * 2
      });
    }

    let raf: number;
    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      nodes.forEach(n => {
        n.x += n.vx; n.y += n.vy; n.pulse += 0.03;
        if (n.x < 0 || n.x > canvas.width)  n.vx *= -1;
        if (n.y < 0 || n.y > canvas.height) n.vy *= -1;
      });
      // connections
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[i].x - nodes[j].x;
          const dy = nodes[i].y - nodes[j].y;
          const dist = Math.sqrt(dx*dx + dy*dy);
          if (dist < 160) {
            ctx.beginPath();
            ctx.moveTo(nodes[i].x, nodes[i].y);
            ctx.lineTo(nodes[j].x, nodes[j].y);
            ctx.strokeStyle = `rgba(33,150,243,${0.25 * (1 - dist / 160)})`;
            ctx.lineWidth = 0.8;
            ctx.stroke();
          }
        }
      }
      // nodes
      nodes.forEach(n => {
        const glow = (Math.sin(n.pulse) + 1) / 2;
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(33,150,243,${0.4 + glow * 0.5})`;
        ctx.fill();
      });
      raf = requestAnimationFrame(draw);
    };
    draw();
    return () => cancelAnimationFrame(raf);
  }, []);
  return <canvas ref={canvasRef} className="absolute inset-0 w-full h-full pointer-events-none" />;
};

// ── Counter animation ──────────────────────────
const AnimatedNumber: React.FC<{ target: number; suffix?: string }> = ({ target, suffix = "" }) => {
  const [val, setVal] = useState(0);
  useEffect(() => {
    let start = 0;
    const step = () => {
      start += Math.ceil((target - start) / 12) || 1;
      setVal(Math.min(start, target));
      if (start < target) requestAnimationFrame(step);
    };
    const t = setTimeout(() => requestAnimationFrame(step), 200);
    return () => clearTimeout(t);
  }, [target]);
  return <>{val.toLocaleString()}{suffix}</>;
};

const stats = [
  { label: "Composants",   value: 180, suffix: "+",  color: "#2196F3", icon: "⚡" },
  { label: "Cours",        value: 24,  suffix: "",   color: "#00BCD4", icon: "📚" },
  { label: "Simulateurs",  value: 8,   suffix: "",   color: "#42A5F5", icon: "🔬" },
  { label: "Communauté",   value: 1200,suffix: "+",  color: "#00E5FF", icon: "👥" },
];

const features = [
  {
    to: "/simulator",
    icon: "🔌",
    title: "Simulateur de Circuits",
    desc: "Concevez et simulez vos circuits électroniques en temps réel, comme TinkerCAD — mais plus puissant.",
    badge: "TinkerCAD-like",
    color: "#1565C0",
  },
  {
    to: "/components",
    icon: "🧩",
    title: "Bibliothèque Composants",
    desc: "Explorez 180+ composants électroniques animés avec fiches techniques, câblage et code prêt à l'emploi.",
    badge: "Interactive",
    color: "#00BCD4",
  },
  {
    to: "/courses",
    icon: "🎓",
    title: "Cours & eLearning",
    desc: "Apprenez Arduino, ESP32, Raspberry Pi, ROS, STM32 et plus — du débutant à l'expert.",
    badge: "eLearning",
    color: "#1976D2",
  },
  {
    to: "/robots",
    icon: "🤖",
    title: "Simulation 3D Robotique",
    desc: "Simulez vos robots en 3D avec Three.js, URDF, IK et trajectoires — reliez vos microcontrôleurs.",
    badge: "3D",
    color: "#42A5F5",
  },
  {
    to: "/projects",
    icon: "💻",
    title: "Éditeur de Code",
    desc: "Compilez et simulez l'exécution de code pour Arduino, ESP32, STM32 directement dans le navigateur.",
    badge: "Compiler",
    color: "#1565C0",
  },
  {
    to: "/community",
    icon: "🌐",
    title: "Communauté",
    desc: "Partagez vos projets, découvrez les créations de la communauté et collaborez avec des passionnés.",
    badge: "Social",
    color: "#00BCD4",
  },
];

const recentActivity = [
  { label: "Simulation ESP32 + DHT22",    status: "ok",    time: "il y a 2 min" },
  { label: "Cours Arduino — Module 5/8",  status: "cours", time: "il y a 1h"    },
  { label: "Projet: Robot suiveur ligne",  status: "ok",    time: "hier"         },
  { label: "Composant: MPU6050 consulté", status: "info",  time: "hier"         },
];

const navigate_hook = (to: string) => { window.location.hash = to.slice(1); };

const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  return (
    <div className="space-y-8 pb-8">
      {/* ── Hero ── */}
      <div className="relative rounded-3xl overflow-hidden"
        style={{ background: "linear-gradient(135deg, #0D1421 0%, #0a1628 50%, #0a1820 100%)", minHeight: 220 }}>
        <CircuitParticles />
        {/* Decorative hexagons */}
        <div className="absolute top-4 right-8 opacity-10">
          <svg viewBox="0 0 120 120" className="w-48 h-48">
            <path d="M60 5 L108 32 L108 88 L60 115 L12 88 L12 32 Z"
              stroke="#2196F3" strokeWidth="2" fill="none"/>
            <path d="M60 20 L96 42 L96 78 L60 100 L24 78 L24 42 Z"
              stroke="#1976D2" strokeWidth="1" fill="none"/>
          </svg>
        </div>
        <div className="relative z-10 p-8 md:p-10">
          <div className="flex items-center gap-3 mb-3">
            <span className="badge badge-blue">v2.0</span>
            <span className="badge badge-cyan">IA Cognito</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-extrabold text-white mb-2 leading-tight">
            Bienvenue sur{" "}
            <span className="gradient-text">CognitoLab</span>
          </h1>
          <p className="text-slate-400 text-base max-w-xl mb-6">
            La plateforme tout-en-un pour concevoir, simuler et programmer vos circuits et microcontrôleurs.
            Accompagné de <strong className="text-cl-blue-4">Cognito</strong>, votre assistant IA.
          </p>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => navigate("/simulator")}
              className="btn-primary px-5 py-2.5 rounded-xl text-sm font-semibold"
            >
              ⚡ Démarrer une simulation
            </button>
            <button
              onClick={() => navigate("/courses")}
              className="btn-ghost px-5 py-2.5 rounded-xl text-sm font-semibold"
            >
              📚 Explorer les cours
            </button>
          </div>
        </div>
      </div>

      {/* ── Stats ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {stats.map(s => (
          <div key={s.label} className="stat-card">
            <div className="text-2xl mb-1">{s.icon}</div>
            <div className="text-2xl font-bold" style={{ color: s.color }}>
              <AnimatedNumber target={s.value} suffix={s.suffix} />
            </div>
            <div className="text-xs text-slate-500 mt-0.5">{s.label}</div>
          </div>
        ))}
      </div>

      {/* ── Features grid ── */}
      <div>
        <h2 className="section-title mb-1">Fonctionnalités</h2>
        <p className="section-sub mb-4">Tout ce dont vous avez besoin pour l'électronique et la programmation embarquée</p>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {features.map(f => (
            <div
              key={f.to}
              className="feature-card cursor-pointer"
              onClick={() => navigate(f.to)}
            >
              <div className="flex items-start gap-3 mb-3">
                <div className="text-2xl">{f.icon}</div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-sm font-bold text-white">{f.title}</h3>
                    <span className="badge badge-blue text-xs">{f.badge}</span>
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">{f.desc}</p>
                </div>
              </div>
              <div className="flex justify-end">
                <span className="text-xs font-medium" style={{ color: f.color }}>
                  Ouvrir →
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Bottom row ── */}
      <div className="grid md:grid-cols-2 gap-4">
        {/* Activity */}
        <div className="glass rounded-2xl p-5">
          <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cl-blue-3 animate-pulse" />
            Activité récente
          </h3>
          <div className="space-y-3">
            {recentActivity.map((a, i) => (
              <div key={i} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${
                    a.status === "ok"    ? "bg-emerald-400" :
                    a.status === "cours" ? "bg-cl-blue-3"   : "bg-cl-cyan"
                  }`} />
                  <span className="text-xs text-slate-300">{a.label}</span>
                </div>
                <span className="text-xs text-slate-600">{a.time}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Progression cours */}
        <div className="glass rounded-2xl p-5">
          <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
            <span className="text-cl-blue-3">📈</span>
            Progression des cours
          </h3>
          <div className="space-y-4">
            {[
              { name: "Arduino pour débutants", pct: 72, color: "blue" as const },
              { name: "ESP32 IoT avancé",        pct: 34, color: "cyan" as const },
              { name: "Robotique industrielle",   pct: 18, color: "blue" as const },
            ].map(c => (
              <div key={c.name}>
                <div className="flex justify-between mb-1">
                  <span className="text-xs text-slate-300">{c.name}</span>
                  <span className="text-xs text-cl-blue-4">{c.pct}%</span>
                </div>
                <ProgressBar value={c.pct} color={c.color} />
              </div>
            ))}
            <button onClick={() => navigate("/courses")} className="btn-ghost w-full text-xs py-2 mt-2 rounded-lg">
              Voir tous les cours →
            </button>
          </div>
        </div>
      </div>

      {/* ── Cognito CTA ── */}
      <div className="relative rounded-2xl overflow-hidden p-6 text-center"
        style={{ background: "linear-gradient(135deg, rgba(21,101,192,0.2), rgba(0,188,212,0.1))", border: "1px solid rgba(33,150,243,0.2)" }}>
        <div className="absolute inset-0 opacity-5"
          style={{ backgroundImage: "radial-gradient(circle, #2196F3 1px, transparent 1px)", backgroundSize: "20px 20px" }} />
        <div className="relative z-10">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-full mb-3 mx-auto"
            style={{ background: "linear-gradient(135deg, #1565C0, #00BCD4)" }}>
            <svg viewBox="0 0 36 36" fill="none" className="w-8 h-8">
              <circle cx="18" cy="18" r="7" stroke="white" strokeWidth="2.5" fill="none"/>
              <line x1="18" y1="4" x2="18" y2="11" stroke="white" strokeWidth="2" strokeLinecap="round"/>
              <line x1="18" y1="25" x2="18" y2="32" stroke="white" strokeWidth="2" strokeLinecap="round"/>
              <line x1="4" y1="18" x2="11" y2="18" stroke="white" strokeWidth="2" strokeLinecap="round"/>
              <line x1="25" y1="18" x2="32" y2="18" stroke="white" strokeWidth="2" strokeLinecap="round"/>
              <circle cx="18" cy="4" r="2.5" fill="white"/>
              <circle cx="18" cy="32" r="2.5" fill="white"/>
              <circle cx="4" cy="18" r="2.5" fill="white"/>
              <circle cx="32" cy="18" r="2.5" fill="white"/>
            </svg>
          </div>
          <h3 className="text-lg font-bold text-white mb-1">Cognito est là pour vous aider</h3>
          <p className="text-sm text-slate-400 mb-4 max-w-md mx-auto">
            Posez vos questions sur l'électronique, la programmation embarquée, le débogage de circuits — Cognito répond instantanément, propulsé par Claude (Anthropic).
          </p>
          <p className="text-xs text-slate-600">Cliquez sur le bouton bleu en bas à droite →</p>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
