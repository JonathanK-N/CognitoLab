import React, { useEffect } from "react";
import { useSimulator } from "@cognitolab/simulator-core";
import type { ComponentInstance } from "@cognitolab/simulator-core";
import { Button } from "@cognitolab/ui";

type Props = {
  preset?: string;
};

const defaultComponents: ComponentInstance[] = [
  {
    id: "led1",
    kind: "led",
    name: "LED",
    position: { x: 120, y: 120 },
    pins: [
      { id: "anode", label: "A", type: "analog" },
      { id: "cathode", label: "K", type: "ground" }
    ],
    properties: { vf: 2 }
  },
  {
    id: "res1",
    kind: "resistor",
    name: "1k",
    position: { x: 200, y: 120 },
    pins: [
      { id: "a", label: "A", type: "analog" },
      { id: "b", label: "B", type: "analog" }
    ],
    properties: { resistance: 1000 }
  }
];

const InternalCanvasSimulator: React.FC<Props> = ({ preset }) => {
  const { canvasRef, result, addComponent } = useSimulator({ timestepMs: 30 });

  useEffect(() => {
    defaultComponents.forEach(addComponent);
  }, [addComponent]);

  const addBreadboard = () => {
    addComponent({
      id: "bb1",
      kind: "breadboard",
      name: "Breadboard",
      position: { x: 320, y: 200 },
      pins: [],
      properties: { preset }
    });
  };

  return (
    <div className="relative border rounded-lg overflow-hidden bg-white">
      <div className="flex items-center justify-between px-3 py-2 border-b bg-slate-50">
        <div className="text-sm text-slate-600">Simulateur interne · {preset}</div>
        <div className="flex gap-2">
          <Button size="sm" variant="ghost" onClick={addBreadboard}>
            Ajouter Breadboard
          </Button>
        </div>
      </div>
      <canvas ref={canvasRef} className="w-full h-[380px] bg-slate-100" />
      {result && (
        <div className="px-3 py-2 text-xs text-slate-600 bg-slate-50 border-t">
          {Object.entries(result.logic)
            .slice(0, 3)
            .map(([k, v]) => (
              <span key={k} className="mr-3">
                {k}: {v}
              </span>
            ))}
        </div>
      )}
    </div>
  );
};

export default InternalCanvasSimulator;
