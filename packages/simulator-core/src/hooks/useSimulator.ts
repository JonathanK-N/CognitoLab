import { useEffect, useRef, useState } from "react";
import { CircuitSimulator } from "../simulator";
import type { ComponentInstance, Wire, SimulationResult, SimulationOptions } from "../types";

export const useSimulator = (options: SimulationOptions = {}) => {
  const [sim] = useState(() => new CircuitSimulator(options));
  const [result, setResult] = useState<SimulationResult | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    if (!canvasRef.current) return;
    sim.attachRenderer(canvasRef.current);
  }, [sim, canvasRef]);

  const addComponent = (component: ComponentInstance) => sim.addComponent(component);
  const addWire = (wire: Wire) => sim.addWire(wire);

  const tick = () => {
    const res = sim.step();
    setResult(res);
    return res;
  };

  useEffect(() => {
    const interval = setInterval(tick, options.timestepMs ?? 30);
    return () => clearInterval(interval);
  });

  return {
    canvasRef,
    result,
    addComponent,
    addWire,
    getState: sim.getState.bind(sim),
    tick
  };
};
