import React, { useState } from "react";
import UnifiedSimulator from "../components/UnifiedSimulator";
import AIAssistantPanel from "../components/AIAssistantPanel";

type BoardId =
  | "arduino-uno" | "arduino-nano" | "arduino-mega"
  | "esp32" | "stm32f103" | "rp2040" | "pico" | "logic-circuits";

const boards: { id: BoardId; label: string; icon: string; color: string; desc: string }[] = [
  { id: "arduino-uno",   label: "Arduino Uno",     icon: "🔵", color: "#1565C0", desc: "ATmega328P · 14 I/O" },
  { id: "arduino-nano",  label: "Arduino Nano",    icon: "🔷", color: "#1976D2", desc: "ATmega328P · compact" },
  { id: "arduino-mega",  label: "Arduino Mega",    icon: "💠", color: "#1565C0", desc: "ATmega2560 · 54 I/O" },
  { id: "esp32",         label: "ESP32",           icon: "📡", color: "#00BCD4", desc: "Xtensa LX6 · WiFi/BT" },
  { id: "stm32f103",     label: "STM32 Blue Pill", icon: "🟣", color: "#7C4DFF", desc: "Cortex-M3 · 72MHz" },
  { id: "rp2040",        label: "RP2040",          icon: "🟢", color: "#00897B", desc: "Dual Cortex-M0+ · 133MHz" },
  { id: "pico",          label: "Raspberry Pico",  icon: "🟡", color: "#F57F17", desc: "RP2040 · MicroPython" },
  { id: "logic-circuits",label: "Logique / Breadboard", icon: "⚡", color: "#42A5F5", desc: "Circuit analogique/digital" },
];

const SimulatorPage: React.FC = () => {
  const [board, setBoard] = useState<BoardId>("arduino-uno");
  const [tab, setTab]     = useState<"simulateur" | "assistant">("simulateur");

  const selected = boards.find(b => b.id === board)!;

  const tabs = [
    { id: "simulateur", label: "🔌 Simulateur",  content: <UnifiedSimulator board={board} /> },
    { id: "assistant",  label: "🧠 Cognito IA",  content: <AIAssistantPanel board={selected.label} embedded /> }
  ];

  return (
    <div className="space-y-5 pb-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="section-title">Simulateur de Circuits</h1>
          <p className="section-sub">Sélectionnez une carte et simulez votre circuit ou code en temps réel</p>
        </div>
        <div className="hidden md:flex items-center gap-2 px-4 py-2 rounded-xl glass text-xs text-cl-blue-4">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          Simulateur actif
        </div>
      </div>

      {/* Board selector */}
      <div>
        <p className="text-xs text-slate-500 mb-3 uppercase tracking-wider font-medium">Choisir la carte</p>
        <div className="flex flex-wrap gap-2">
          {boards.map(b => (
            <button
              key={b.id}
              onClick={() => setBoard(b.id)}
              className={`board-chip flex items-center gap-2 ${board === b.id ? "active" : ""}`}
              title={b.desc}
            >
              <span>{b.icon}</span>
              <span>{b.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Selected board info */}
      <div className="flex items-center gap-4 px-4 py-3 rounded-xl"
        style={{ background: "rgba(21,101,192,0.1)", border: "1px solid rgba(33,150,243,0.2)" }}>
        <div className="text-2xl">{selected.icon}</div>
        <div>
          <p className="text-sm font-bold text-white">{selected.label}</p>
          <p className="text-xs text-slate-400">{selected.desc}</p>
        </div>
        <div className="ml-auto flex gap-2">
          <span className="badge badge-blue">Simulation</span>
          <span className="badge badge-cyan">Code Live</span>
        </div>
      </div>

      {/* Simulator / AI tabs */}
      <div className="glass rounded-2xl overflow-hidden" style={{ minHeight: 500 }}>
        {/* Tab bar */}
        <div className="flex border-b border-cl-blue/10">
          {tabs.map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id as any)}
              className={`px-5 py-3 text-sm font-medium transition-all ${
                tab === t.id
                  ? "text-cl-blue-3 border-b-2 border-cl-blue-3 bg-cl-blue/5"
                  : "text-slate-500 hover:text-slate-300"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
        <div className="p-4">
          {tabs.find(t => t.id === tab)?.content}
        </div>
      </div>
    </div>
  );
};

export default SimulatorPage;
