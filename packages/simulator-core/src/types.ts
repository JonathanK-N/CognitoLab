export type ComponentKind =
  | "led"
  | "resistor"
  | "capacitor"
  | "diode"
  | "transistor"
  | "ic"
  | "wire"
  | "power"
  | "ground"
  | "microcontroller"
  | "sensor"
  | "actuator";

export type Pin = {
  id: string;
  label: string;
  net?: string;
  type: "analog" | "digital" | "power" | "ground";
};

export type ComponentInstance = {
  id: string;
  kind: ComponentKind;
  name: string;
  pins: Pin[];
  position: { x: number; y: number; z?: number };
  rotation?: number;
  properties?: Record<string, number | string | boolean>;
};

export type Wire = {
  id: string;
  from: { componentId: string; pinId: string };
  to: { componentId: string; pinId: string };
  color?: string;
};

export type SimulationResult = {
  timestamp: number;
  voltages: Record<string, number>;
  currents: Record<string, number>;
  logic: Record<string, 0 | 1>;
};

export type SimulationOptions = {
  timestepMs?: number;
  supplyVoltage?: number;
};
