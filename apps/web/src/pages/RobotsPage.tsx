import React, { useState } from "react";
import { Card, Section, Button } from "@cognitolab/ui";
import { Robot3DSimulator } from "@cognitolab/robot-simulation-engine";
import catalog from "../../../robots/robotCatalog.json";

type Catalog = Record<string, { name: string; vendor: string; dof: number }>;

const RobotsPage: React.FC = () => {
  const [selected, setSelected] = useState<string>(Object.keys(catalog)[0]);

  return (
    <div className="space-y-6">
      <Section title="Robotique 3D" description="Moteur Three.js + URDF, IK, trajectoires.">
        <div className="grid md:grid-cols-3 gap-4">
          <Card title="Catalogue">
            <div className="space-y-2 max-h-[460px] overflow-auto">
              {Object.entries(catalog as Catalog).map(([id, r]) => (
                <button
                  key={id}
                  onClick={() => setSelected(id)}
                  className={`w-full text-left px-3 py-2 rounded-md border ${
                    selected === id ? "border-indigo-500 bg-indigo-50" : "border-slate-200"
                  }`}
                >
                  <p className="font-semibold">{r.name}</p>
                  <p className="text-xs text-slate-500">
                    {r.vendor} · {r.dof} axes
                  </p>
                </button>
              ))}
            </div>
          </Card>
          <Card className="md:col-span-2" title="Simulation 3D">
            <Robot3DSimulator robotId={selected} height={420} />
            <div className="mt-3 flex gap-2">
              <Button size="sm">Jouer trajectoire</Button>
              <Button size="sm" variant="secondary">
                Lier microcontrôleur
              </Button>
            </div>
          </Card>
        </div>
      </Section>
    </div>
  );
};

export default RobotsPage;
