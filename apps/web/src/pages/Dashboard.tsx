import React from "react";
import { Card, Section, ProgressBar } from "@cognitolab/ui";

const DashboardPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <Section title="Bienvenue sur CognitoLab" description="Simulation circuits, microcontrôleurs et robotique.">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card title="Simulations" subtitle="Dernières sessions">
            <div className="space-y-2 text-sm text-slate-600">
              <div className="flex justify-between">
                <span>Arduino + LED</span>
                <span className="text-emerald-600">OK</span>
              </div>
              <div className="flex justify-between">
                <span>ESP32 + servo</span>
                <span className="text-amber-600">En cours</span>
              </div>
              <div className="flex justify-between">
                <span>STM32 + robot UR5</span>
                <span className="text-emerald-600">OK</span>
              </div>
            </div>
          </Card>
          <Card title="Progression cours" subtitle="LMS">
            <div className="space-y-4">
              <div>
                <p className="text-sm text-slate-500">Arduino basics</p>
                <ProgressBar value={72} />
              </div>
              <div>
                <p className="text-sm text-slate-500">Robotique industrielle</p>
                <ProgressBar value={38} color="amber" />
              </div>
            </div>
          </Card>
          <Card title="Robotique" subtitle="Sessions récentes">
            <ul className="text-sm text-slate-600 space-y-1">
              <li>UR5 pick&place</li>
              <li>KUKA iiwa7 calibration</li>
              <li>MyCobot 320 gripper</li>
            </ul>
          </Card>
        </div>
      </Section>
    </div>
  );
};

export default DashboardPage;
