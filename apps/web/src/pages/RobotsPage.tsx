import React, { useState } from "react";
import { Robot3DSimulator } from "@cognitolab/robot-simulation-engine";
import catalog from "../../../robots/robotCatalog.json";

type Catalog = Record<string, { name: string; vendor: string; dof: number }>;

const RobotsPage: React.FC = () => {
  const [selected, setSelected] = useState<string>(Object.keys(catalog)[0]);
  const robot = (catalog as Catalog)[selected];

  return (
    <div className="space-y-5 pb-8">
      {/* Header */}
      <div>
        <h1 className="section-title">Simulation Robotique 3D</h1>
        <p className="section-sub">Simulez vos robots industriels et personnels en 3D avec Three.js + URDF</p>
      </div>

      <div className="grid md:grid-cols-3 gap-4">
        {/* Robot catalog */}
        <div className="glass rounded-2xl overflow-hidden">
          <div className="px-4 py-3 border-b border-cl-blue/10">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Catalogue robots</p>
          </div>
          <div className="p-3 space-y-1.5 max-h-[500px] overflow-auto">
            {Object.entries(catalog as Catalog).map(([id, r]) => (
              <button
                key={id}
                onClick={() => setSelected(id)}
                className={`w-full text-left px-3 py-2.5 rounded-xl transition-all ${
                  selected === id
                    ? "bg-cl-blue/15 border border-cl-blue/35 text-white"
                    : "text-slate-400 hover:bg-cl-dark-4/50 border border-transparent"
                }`}
              >
                <p className="text-xs font-bold leading-snug">{r.name}</p>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-xs text-slate-500">{r.vendor}</span>
                  <span className="badge badge-blue">{r.dof} DOF</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* 3D Viewer */}
        <div className="md:col-span-2 glass rounded-2xl overflow-hidden">
          <div className="px-4 py-3 border-b border-cl-blue/10 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-base font-bold text-white">🤖 {robot.name}</span>
              <span className="badge badge-cyan">{robot.vendor}</span>
              <span className="badge badge-blue">{robot.dof} axes</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs text-emerald-400">Simulation 3D</span>
            </div>
          </div>

          <div className="relative" style={{ background: "#060a14" }}>
            <Robot3DSimulator robotId={selected} height={400} />
          </div>

          <div className="p-4 flex flex-wrap gap-2 border-t border-cl-blue/10">
            <button className="btn-primary text-xs px-4 py-2 rounded-lg">▶ Jouer trajectoire</button>
            <button className="btn-ghost text-xs px-4 py-2 rounded-lg">🔗 Lier microcontrôleur</button>
            <button className="btn-ghost text-xs px-4 py-2 rounded-lg">📐 Cinématique inverse</button>
            <button className="btn-ghost text-xs px-4 py-2 rounded-lg">📹 Enregistrer</button>
          </div>
        </div>
      </div>

      {/* Info panel */}
      <div className="glass rounded-2xl p-5">
        <h3 className="text-sm font-bold text-white mb-3">Fonctionnalités avancées</h3>
        <div className="grid md:grid-cols-4 gap-4">
          {[
            { icon: "📐", title: "IK Solver",       desc: "Cinématique inverse temps réel" },
            { icon: "🎬", title: "Trajectoires",     desc: "Planification et replay de mouvements" },
            { icon: "🔗", title: "MCU Bridge",       desc: "Liaison avec Arduino / ESP32" },
            { icon: "📊", title: "ROS 2 Export",     desc: "Export URDF et topics ROS" },
          ].map(f => (
            <div key={f.title} className="flex items-start gap-3 p-3 rounded-xl"
              style={{ background: "rgba(33,150,243,0.05)", border: "1px solid rgba(33,150,243,0.12)" }}>
              <span className="text-xl">{f.icon}</span>
              <div>
                <p className="text-xs font-bold text-white">{f.title}</p>
                <p className="text-xs text-slate-400 mt-0.5">{f.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default RobotsPage;
