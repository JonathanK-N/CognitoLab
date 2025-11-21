import React, { useMemo, useState } from "react";
import { Card, Section, Tabs } from "@cognitolab/ui";
import UnifiedSimulator from "../components/UnifiedSimulator";
import AIAssistantPanel from "../components/AIAssistantPanel";

type BoardId =
  | "arduino-uno"
  | "arduino-nano"
  | "arduino-mega"
  | "esp32"
  | "stm32f103"
  | "rp2040"
  | "pico"
  | "logic-circuits";

const boardOptions: { id: BoardId; label: string }[] = [
  { id: "arduino-uno", label: "Arduino Uno" },
  { id: "arduino-nano", label: "Arduino Nano" },
  { id: "arduino-mega", label: "Arduino Mega" },
  { id: "esp32", label: "ESP32" },
  { id: "stm32f103", label: "STM32F103" },
  { id: "rp2040", label: "RP2040" },
  { id: "pico", label: "Raspberry Pi Pico" },
  { id: "logic-circuits", label: "Logique / Breadboard" }
];

const SimulatorPage: React.FC = () => {
  const [board, setBoard] = useState<BoardId>("arduino-uno");
  const [tab, setTab] = useState<"simulateur" | "assistant">("simulateur");

  const tabs = useMemo(
    () => [
      { id: "simulateur", label: "Simulateur", content: <UnifiedSimulator board={board} /> },
      { id: "assistant", label: "Assistant IA", content: <AIAssistantPanel board={board} /> }
    ],
    [board]
  );

  return (
    <div className="space-y-6">
      <Section title="Simulateur" description="Wokwi, Renode ou simulateur interne Crocclip-like.">
        <Card>
          <div className="flex gap-2 flex-wrap mb-4">
            {boardOptions.map((option) => {
              const isActive = board === option.id;
              return (
                <button
                  key={option.id}
                  onClick={() => setBoard(option.id)}
                  className={
                    "px-3 py-1.5 rounded-full text-sm border transition " +
                    (isActive
                      ? "bg-indigo-600 text-white border-indigo-600 shadow-sm"
                      : "bg-white text-slate-700 hover:bg-slate-100 border-slate-200")
                  }
                  aria-pressed={isActive}
                >
                  {option.label}
                </button>
              );
            })}
          </div>
          <Tabs tabs={tabs} selected={tab} onSelect={(id) => setTab(id as "simulateur" | "assistant")} />
        </Card>
      </Section>
    </div>
  );
};

export default SimulatorPage;
