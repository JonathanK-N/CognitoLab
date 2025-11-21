import React from "react";
import { Card, Button } from "@cognitolab/ui";

const RenodeWasmEmbed: React.FC<{ board: string }> = ({ board }) => {
  const renodeUrl = "https://renode.io/showcase/";
  return (
    <Card title="Renode WebAssembly (placeholder)">
      <p className="text-sm text-slate-600 mb-3">
        Renode WASM chargé pour la carte {board}. Intégration temps réel via WebSocket + Renode agent.
      </p>
      <div className="aspect-video bg-slate-900 text-slate-200 rounded-lg flex items-center justify-center">
        <span>Instance Renode WASM</span>
      </div>
      <Button className="mt-3" variant="secondary" onClick={() => window.open(renodeUrl, "_blank")}>
        Ouvrir Renode
      </Button>
    </Card>
  );
};

export default RenodeWasmEmbed;
