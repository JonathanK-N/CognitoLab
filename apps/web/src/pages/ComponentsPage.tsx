import React from "react";
import { Card, Section, Button } from "@cognitolab/ui";
import { icons } from "@cognitolab/components-svg";

const ComponentsPage: React.FC = () => {
  const assetBase = new URL("../../packages/libraries/components-svg/", import.meta.url);
  return (
    <div className="space-y-6">
      <Section
        title="Composants / Capteurs / Actionneurs"
        description="Icônes SVG/PNG réels, schémas de câblage, snippets Arduino & MicroPython."
      >
        <div className="grid md:grid-cols-3 gap-4">
          {icons.map((icon) => (
            <Card key={icon.id} title={icon.name} subtitle={icon.category}>
              <div className="flex items-center gap-3">
                <img
                  src={new URL(icon.file, assetBase).href}
                  alt={icon.name}
                  className="w-16 h-16 bg-slate-100 rounded-lg object-contain p-2"
                />
                <div className="text-sm text-slate-600">
                  <p>Code Arduino:</p>
                  <code className="block bg-slate-100 rounded px-2 py-1 text-xs mt-1">
                    // setup {icon.name}
                  </code>
                </div>
              </div>
              <div className="mt-3 flex gap-2">
                <Button size="sm" variant="secondary">
                  Voir câblage
                </Button>
                <Button size="sm" variant="ghost">
                  Simuler
                </Button>
              </div>
            </Card>
          ))}
        </div>
      </Section>
    </div>
  );
};

export default ComponentsPage;
