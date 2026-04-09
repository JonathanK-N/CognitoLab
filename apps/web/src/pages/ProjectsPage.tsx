import React, { useState } from "react";

type Project = {
  id: string;
  title: string;
  board: string;
  code: string;
  status: "draft" | "running" | "done";
  createdAt: string;
};

const boardOptions = [
  { value: "arduino-uno",   label: "Arduino Uno" },
  { value: "arduino-mega",  label: "Arduino Mega" },
  { value: "arduino-nano",  label: "Arduino Nano" },
  { value: "esp32",         label: "ESP32" },
  { value: "stm32f103",     label: "STM32F103" },
  { value: "rp2040",        label: "RP2040 / Pico" },
];

const defaultProjects: Project[] = [
  {
    id: "p1",
    title: "ESP32 WiFi + LED blinker",
    board: "esp32",
    status: "done",
    createdAt: "2025-04-01",
    code: `#include <WiFi.h>\n\nconst char* ssid = "MonWiFi";\nconst char* password = "motdepasse";\n\nvoid setup() {\n  Serial.begin(115200);\n  pinMode(2, OUTPUT);\n  WiFi.begin(ssid, password);\n  while (WiFi.status() != WL_CONNECTED) {\n    delay(500);\n    Serial.print(".");\n  }\n  Serial.println("Connecté! IP: ");\n  Serial.println(WiFi.localIP());\n}\n\nvoid loop() {\n  digitalWrite(2, HIGH);\n  delay(500);\n  digitalWrite(2, LOW);\n  delay(500);\n}`
  },
  {
    id: "p2",
    title: "Arduino Température DHT22",
    board: "arduino-uno",
    status: "running",
    createdAt: "2025-04-05",
    code: `#include <DHT.h>\n#define DHTPIN 2\n#define DHTTYPE DHT22\n\nDHT dht(DHTPIN, DHTTYPE);\n\nvoid setup() {\n  Serial.begin(9600);\n  dht.begin();\n}\n\nvoid loop() {\n  float h = dht.readHumidity();\n  float t = dht.readTemperature();\n  if (!isnan(h) && !isnan(t)) {\n    Serial.print("Temp: ");\n    Serial.print(t);\n    Serial.print("°C  Hum: ");\n    Serial.println(h);\n  }\n  delay(2000);\n}`
  }
];

const statusLabel: Record<string, { text: string; cls: string }> = {
  draft:   { text: "Brouillon",  cls: "badge-blue"  },
  running: { text: "En cours",   cls: "badge-amber" },
  done:    { text: "Terminé",    cls: "badge-green" },
};

const ProjectsPage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>(defaultProjects);
  const [title, setTitle]       = useState("");
  const [board, setBoard]       = useState("arduino-uno");
  const [code, setCode]         = useState("void setup() {\n  // Initialisation\n}\n\nvoid loop() {\n  // Code principal\n}");
  const [activeProject, setActiveProject] = useState<Project | null>(defaultProjects[0]);
  const [output, setOutput]     = useState<string[]>([]);
  const [running, setRunning]   = useState(false);
  const [tab, setTab]           = useState<"editor" | "output">("editor");

  const createProject = () => {
    if (!title.trim()) return;
    const p: Project = {
      id: crypto.randomUUID(),
      title: title.trim(),
      board,
      code,
      status: "draft",
      createdAt: new Date().toISOString().slice(0, 10)
    };
    setProjects(prev => [p, ...prev]);
    setActiveProject(p);
    setTitle("");
  };

  const simulate = () => {
    if (!activeProject) return;
    setRunning(true);
    setTab("output");
    setOutput([
      `[CognitoLab] Compilation pour ${activeProject.board}...`,
      `[OK] Taille du programme: 3.2 Ko / 32 Ko`,
      `[OK] Mémoire globale: 248 octets / 2048 octets`,
      `[UPLOAD] Téléversement en simulation...`,
      `[RUN] Programme démarré sur ${activeProject.board}`,
      `--- Moniteur série (9600 bauds) ---`,
    ]);
    const lines = [
      "Setup exécuté.",
      "Loop() → itération 1",
      "Loop() → itération 2",
      "Loop() → itération 3",
    ];
    lines.forEach((l, i) => {
      setTimeout(() => {
        setOutput(prev => [...prev, l]);
        if (i === lines.length - 1) setRunning(false);
      }, 600 * (i + 1));
    });
  };

  return (
    <div className="space-y-5 pb-8">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <h1 className="section-title">Éditeur de Projets</h1>
          <p className="section-sub">Écrivez, compilez et simulez votre code microcontrôleur</p>
        </div>
        <button onClick={createProject} disabled={!title.trim()} className="btn-primary px-4 py-2 text-sm rounded-xl">
          + Nouveau projet
        </button>
      </div>

      <div className="grid md:grid-cols-3 gap-4">
        {/* Sidebar: project list + new */}
        <div className="space-y-3">
          {/* New project form */}
          <div className="glass rounded-xl p-4 space-y-2">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">Nouveau projet</p>
            <input
              value={title}
              onChange={e => setTitle(e.target.value)}
              placeholder="Nom du projet"
              className="cl-input"
            />
            <select value={board} onChange={e => setBoard(e.target.value)} className="cl-select">
              {boardOptions.map(o => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
            <button onClick={createProject} disabled={!title.trim()} className="btn-primary w-full text-sm py-2 rounded-lg">
              Créer
            </button>
          </div>

          {/* Project list */}
          <div className="space-y-2">
            {projects.map(p => (
              <button
                key={p.id}
                onClick={() => { setActiveProject(p); setCode(p.code); setTab("editor"); setOutput([]); }}
                className={`w-full text-left p-3 rounded-xl transition-all ${
                  activeProject?.id === p.id
                    ? "border border-cl-blue/40 bg-cl-blue/10"
                    : "glass-light hover:bg-cl-dark-4/50"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <p className="text-xs font-bold text-white truncate flex-1 mr-2">{p.title}</p>
                  <span className={`badge ${statusLabel[p.status].cls}`}>{statusLabel[p.status].text}</span>
                </div>
                <p className="text-xs text-slate-500">{p.board} · {p.createdAt}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Editor area */}
        <div className="md:col-span-2 glass rounded-2xl overflow-hidden flex flex-col" style={{ minHeight: 520 }}>
          {/* Toolbar */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-cl-blue/10">
            <div className="flex items-center gap-3">
              <span className="text-sm font-bold text-white">
                {activeProject ? activeProject.title : "Aucun projet sélectionné"}
              </span>
              {activeProject && (
                <span className="badge badge-blue">{activeProject.board}</span>
              )}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setTab("editor")}
                className={`text-xs px-3 py-1.5 rounded-lg transition-all ${tab === "editor" ? "btn-primary" : "btn-ghost"}`}
              >
                📝 Éditeur
              </button>
              <button
                onClick={() => setTab("output")}
                className={`text-xs px-3 py-1.5 rounded-lg transition-all ${tab === "output" ? "btn-primary" : "btn-ghost"}`}
              >
                📟 Console
              </button>
              <button
                onClick={simulate}
                disabled={!activeProject || running}
                className="btn-cyan text-xs px-4 py-1.5 rounded-lg"
              >
                {running ? "⟳ En cours..." : "▶ Simuler"}
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 p-4 flex flex-col">
            {tab === "editor" ? (
              <textarea
                className="code-area flex-1 w-full"
                style={{ minHeight: 400 }}
                value={activeProject ? code : "// Sélectionnez ou créez un projet"}
                onChange={e => setCode(e.target.value)}
                spellCheck={false}
                readOnly={!activeProject}
              />
            ) : (
              <div className="flex-1 bg-black/60 rounded-xl p-4 font-mono text-xs text-emerald-400 overflow-auto"
                style={{ minHeight: 400 }}>
                {output.length === 0 ? (
                  <p className="text-slate-600">Console vide — lancez une simulation pour voir la sortie.</p>
                ) : (
                  output.map((l, i) => (
                    <div key={i} className={l.startsWith("[OK]") ? "text-emerald-400" : l.startsWith("[RUN]") ? "text-cl-cyan-3" : l.startsWith("[UPLOAD]") ? "text-cl-blue-4" : l.startsWith("[CognitoLab]") ? "text-cl-blue-3" : "text-slate-300"}>
                      {l}
                    </div>
                  ))
                )}
                {running && <span className="inline-block animate-pulse text-emerald-400">▋</span>}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProjectsPage;
