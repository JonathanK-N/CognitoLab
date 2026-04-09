import React from "react";
import { useNavigate } from "react-router-dom";

const team = [
  { name: "Jonathan K-N",  role: "Fondateur & Lead Engineer",  avatar: "JK", color: "#1565C0" },
  { name: "Équipe Cognito", role: "R&D Intelligence Artificielle", avatar: "CI", color: "#00BCD4" },
];

const milestones = [
  { year: "2023", label: "Fondation de Cognito Inc.",     icon: "🚀" },
  { year: "2024", label: "Lancement de CognitoLab v1.0",  icon: "⚡" },
  { year: "2025", label: "Intégration de l'IA Cognito",   icon: "🧠" },
  { year: "2025", label: "CognitoLab v2.0 — Refonte UI",  icon: "✨" },
];

const tech = [
  { name: "React + TypeScript", icon: "⚛",  desc: "Interface utilisateur" },
  { name: "Vite",               icon: "⚡",  desc: "Build & dev server" },
  { name: "Three.js + URDF",    icon: "🌐",  desc: "Simulation 3D robotique" },
  { name: "Wokwi / Renode",     icon: "🔌",  desc: "Simulateurs microcontrôleurs" },
  { name: "Claude (Anthropic)", icon: "🧠",  desc: "IA Cognito" },
  { name: "Node.js + Express",  icon: "🖥",   desc: "API backend" },
  { name: "TailwindCSS",        icon: "🎨",  desc: "Design system" },
  { name: "MongoDB",            icon: "🍃",  desc: "Base de données" },
];

const AboutPage: React.FC = () => {
  const navigate = useNavigate();
  return (
    <div className="space-y-8 pb-10 max-w-4xl mx-auto">
      {/* Hero */}
      <div className="relative rounded-3xl overflow-hidden text-center py-14 px-8"
        style={{ background: "linear-gradient(135deg, #0D1421 0%, #0a1628 60%, #061220 100%)" }}>
        {/* Grid */}
        <div className="absolute inset-0 opacity-10"
          style={{
            backgroundImage: "linear-gradient(rgba(33,150,243,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(33,150,243,0.06) 1px, transparent 1px)",
            backgroundSize: "30px 30px"
          }} />
        {/* Glow */}
        <div className="absolute inset-0 pointer-events-none"
          style={{ background: "radial-gradient(circle at 50% 40%, rgba(21,101,192,0.18) 0%, transparent 55%)" }} />

        <div className="relative z-10">
          <div className="flex justify-center mb-6">
            <div className="w-20 h-20 rounded-2xl flex items-center justify-center"
              style={{ background: "linear-gradient(135deg, #1565C0, #00BCD4)", boxShadow: "0 0 40px rgba(33,150,243,0.4)" }}>
              <img src="/logo.svg" alt="CognitoLab" className="w-14 h-14" />
            </div>
          </div>
          <h1 className="text-4xl font-extrabold text-white mb-2">
            <span className="gradient-text">CognitoLab</span>
          </h1>
          <p className="text-lg text-cl-blue-4 font-medium mb-4">La plateforme électronique intelligente</p>
          <p className="text-slate-400 text-sm max-w-xl mx-auto leading-relaxed">
            CognitoLab regroupe tout ce dont vous avez besoin pour concevoir, simuler, apprendre et programmer
            des circuits électroniques et microcontrôleurs — enrichi par l'intelligence artificielle <strong className="text-cl-blue-4">Cognito</strong>.
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <span className="badge badge-blue">v2.0</span>
            <span className="badge badge-cyan">IA Cognito</span>
            <span className="badge badge-green">Open Beta</span>
          </div>
        </div>
      </div>

      {/* Vision */}
      <div className="glass rounded-2xl p-7">
        <h2 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
          <span className="text-cl-blue-3">🎯</span> Notre Vision
        </h2>
        <p className="text-slate-300 text-sm leading-relaxed mb-4">
          Nous croyons que <strong className="text-white">l'électronique et la programmation embarquée</strong> doivent être accessibles
          à tous — du lycéen curieux à l'ingénieur confirmé. CognitoLab supprime les barrières en offrant un
          environnement tout-en-un : simulateur de circuit, bibliothèque de composants, cours interactifs,
          compilateur en ligne et communauté, le tout accompagné d'un assistant IA expert.
        </p>
        <div className="grid md:grid-cols-3 gap-4">
          {[
            { icon: "🔬", title: "Simulation réelle",    desc: "Des simulateurs fidèles au matériel (Wokwi, Renode, Three.js)" },
            { icon: "🎓", title: "Apprentissage guidé",  desc: "Cours structurés du débutant à l'expert, avec Cognito comme tuteur" },
            { icon: "🌐", title: "Communauté active",    desc: "Partagez, inspirez-vous, collaborez avec des milliers de makers" },
          ].map(v => (
            <div key={v.title} className="p-4 rounded-xl"
              style={{ background: "rgba(33,150,243,0.06)", border: "1px solid rgba(33,150,243,0.12)" }}>
              <div className="text-2xl mb-2">{v.icon}</div>
              <p className="text-sm font-bold text-white mb-1">{v.title}</p>
              <p className="text-xs text-slate-400 leading-relaxed">{v.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Milestones */}
      <div className="glass rounded-2xl p-7">
        <h2 className="text-lg font-bold text-white mb-5 flex items-center gap-2">
          <span className="text-cl-cyan">📅</span> Histoire
        </h2>
        <div className="relative">
          <div className="absolute left-5 top-0 bottom-0 w-px"
            style={{ background: "linear-gradient(to bottom, #1565C0, #00BCD4)" }} />
          <div className="space-y-5 pl-12">
            {milestones.map((m, i) => (
              <div key={i} className="relative">
                <div className="absolute -left-7 w-4 h-4 rounded-full flex items-center justify-center"
                  style={{ background: "linear-gradient(135deg, #1565C0, #00BCD4)", top: "2px" }}>
                  <div className="w-2 h-2 rounded-full bg-white" />
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-lg">{m.icon}</span>
                  <div>
                    <p className="text-xs text-cl-blue-4 font-medium">{m.year}</p>
                    <p className="text-sm text-white font-semibold">{m.label}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Team */}
      <div className="glass rounded-2xl p-7">
        <h2 className="text-lg font-bold text-white mb-5 flex items-center gap-2">
          <span className="text-cl-blue-3">👥</span> Équipe
        </h2>
        <div className="flex flex-wrap gap-4">
          {team.map(m => (
            <div key={m.name} className="flex items-center gap-3 px-4 py-3 rounded-xl"
              style={{ background: "rgba(33,150,243,0.07)", border: "1px solid rgba(33,150,243,0.15)" }}>
              <div className="w-10 h-10 rounded-full flex items-center justify-center font-bold text-white text-sm"
                style={{ background: `linear-gradient(135deg, ${m.color}, #00BCD4)` }}>
                {m.avatar}
              </div>
              <div>
                <p className="text-sm font-bold text-white">{m.name}</p>
                <p className="text-xs text-slate-400">{m.role}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Tech stack */}
      <div className="glass rounded-2xl p-7">
        <h2 className="text-lg font-bold text-white mb-5 flex items-center gap-2">
          <span className="text-cl-cyan">🛠</span> Stack Technologique
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {tech.map(t => (
            <div key={t.name} className="flex items-center gap-2 p-3 rounded-xl"
              style={{ background: "rgba(33,150,243,0.05)", border: "1px solid rgba(33,150,243,0.1)" }}>
              <span className="text-xl">{t.icon}</span>
              <div>
                <p className="text-xs font-bold text-white">{t.name}</p>
                <p className="text-xs text-slate-500">{t.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Cognito Inc. footer */}
      <div className="relative rounded-2xl overflow-hidden text-center py-8 px-6"
        style={{ background: "linear-gradient(135deg, rgba(21,101,192,0.15), rgba(0,188,212,0.08))", border: "1px solid rgba(33,150,243,0.2)" }}>
        <div className="absolute inset-0 opacity-5"
          style={{ backgroundImage: "radial-gradient(circle, #2196F3 1px, transparent 1px)", backgroundSize: "18px 18px" }} />
        <div className="relative z-10">
          <div className="inline-flex items-center gap-2 mb-3">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center"
              style={{ background: "linear-gradient(135deg, #1565C0, #00BCD4)" }}>
              <img src="/logo.svg" alt="CognitoLab" className="w-6 h-6" />
            </div>
            <span className="text-white font-bold text-base">CognitoLab</span>
          </div>
          <p className="text-sm text-slate-300 mb-1">
            Propulsé par <strong className="text-cl-blue-4">Cognito Inc.</strong> · Tous droits réservés © {new Date().getFullYear()}
          </p>
          <p className="text-xs text-slate-500 mb-4">
            L'assistant IA Cognito est propulsé par Claude, un modèle d'intelligence artificielle d'Anthropic.
          </p>
          <div className="flex justify-center gap-3">
            <button onClick={() => navigate("/")} className="btn-primary text-xs px-5 py-2 rounded-lg">
              ← Retour à l'accueil
            </button>
            <button onClick={() => navigate("/community")} className="btn-ghost text-xs px-5 py-2 rounded-lg">
              Rejoindre la communauté
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AboutPage;
