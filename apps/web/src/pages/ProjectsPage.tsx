import React, { useState } from "react";
import { Card, Section, Button, ProgressBar } from "@cognitolab/ui";

type Project = {
  id: string;
  title: string;
  board: string;
  code: string;
};

const ProjectsPage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([
    {
      id: "p1",
      title: "ESP32 WiFi + LED",
      board: "esp32",
      code: "void setup(){ pinMode(2, OUTPUT);} void loop(){ digitalWrite(2, HIGH); delay(500); digitalWrite(2, LOW); delay(500);} "
    }
  ]);
  const [title, setTitle] = useState("");
  const [board, setBoard] = useState("arduino-uno");
  const [code, setCode] = useState("// Ton code ici");

  const createProject = () => {
    setProjects([...projects, { id: crypto.randomUUID(), title, board, code }]);
    setTitle("");
    setCode("// Ton code ici");
  };

  return (
    <div className="space-y-6">
      <Section title="Projets utilisateurs" description="Code + simulation en un clic, partage cloud.">
        <div className="grid md:grid-cols-2 gap-4">
          <Card title="Nouveau projet">
            <div className="space-y-3">
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Titre"
                className="w-full border rounded px-3 py-2"
              />
              <select value={board} onChange={(e) => setBoard(e.target.value)} className="w-full border rounded px-3 py-2">
                <option value="arduino-uno">Arduino Uno</option>
                <option value="esp32">ESP32</option>
                <option value="stm32">STM32</option>
              </select>
              <textarea
                value={code}
                onChange={(e) => setCode(e.target.value)}
                rows={8}
                className="w-full border rounded px-3 py-2 font-mono text-xs"
              />
              <div className="flex gap-2">
                <Button size="sm" onClick={createProject}>
                  Créer et simuler
                </Button>
                <Button size="sm" variant="ghost">
                  Exporter
                </Button>
              </div>
            </div>
          </Card>
          <Card title="Projets cloud">
            <div className="space-y-3">
              {projects.map((p) => (
                <div key={p.id} className="p-3 border rounded-md bg-white">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-slate-900">{p.title}</p>
                      <p className="text-xs text-slate-500">Board: {p.board}</p>
                    </div>
                    <Button size="sm" variant="secondary">
                      Simuler
                    </Button>
                  </div>
                  <ProgressBar value={40} className="mt-2" />
                  <pre className="text-xs bg-slate-900 text-slate-100 p-2 rounded mt-2 overflow-auto">{p.code}</pre>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </Section>
    </div>
  );
};

export default ProjectsPage;
