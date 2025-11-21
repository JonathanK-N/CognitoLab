import React from "react";
import InternalCanvasSimulator from "./internal/InternalCanvasSimulator";
import WokwiFrame from "./external/WokwiFrame";
import RenodeWasmEmbed from "./external/RenodeWasmEmbed";

const simulatorMap: Record<"wokwi" | "renode" | "internal", string[]> = {
  wokwi: ["arduino-uno", "arduino-mega", "arduino-nano", "esp32", "attiny85", "nano-esp32"],
  renode: ["stm32", "stm32f103", "stm32f401", "rp2040", "pico", "nrf52", "cortex-m", "riscv"],
  internal: ["analog", "digital", "transistors", "logic-circuits", "breadboard"]
};

export type UnifiedSimulatorProps = {
  board: string;
};

const UnifiedSimulator: React.FC<UnifiedSimulatorProps> = ({ board }) => {
  const provider =
    simulatorMap.wokwi.includes(board) || board.startsWith("arduino")
      ? "wokwi"
      : simulatorMap.renode.includes(board)
      ? "renode"
      : "internal";

  if (provider === "wokwi") return <WokwiFrame board={board} />;
  if (provider === "renode") return <RenodeWasmEmbed board={board} />;
  return <InternalCanvasSimulator preset={board} />;
};

export default UnifiedSimulator;
