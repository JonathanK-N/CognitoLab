import type {
  ComponentInstance,
  SimulationOptions,
  SimulationResult,
  Wire
} from "../types";

type NodeState = {
  voltage: number;
  current: number;
  logic: 0 | 1;
};

export class SimulationEngine {
  private timestepMs: number;
  private supplyVoltage: number;
  private nets: Map<string, NodeState> = new Map();

  constructor(opts: SimulationOptions = {}) {
    this.timestepMs = opts.timestepMs ?? 5;
    this.supplyVoltage = opts.supplyVoltage ?? 5;
  }

  private initNets(components: ComponentInstance[], wires: Wire[]) {
    this.nets.clear();
    for (const wire of wires) {
      const key = this.getNetKey(wire);
      if (!this.nets.has(key)) {
        this.nets.set(key, { voltage: 0, current: 0, logic: 0 });
      }
    }

    // assign supply for power pins as starter
    for (const comp of components) {
      for (const pin of comp.pins) {
        if (pin.type === "power") {
          const key = pin.net ?? `${comp.id}:${pin.id}`;
          this.nets.set(key, { voltage: this.supplyVoltage, current: 0, logic: 1 });
        }
        if (pin.type === "ground") {
          const key = pin.net ?? `${comp.id}:${pin.id}`;
          this.nets.set(key, { voltage: 0, current: 0, logic: 0 });
        }
      }
    }
  }

  private getNetKey(wire: Wire) {
    return `${wire.from.componentId}:${wire.from.pinId}-${wire.to.componentId}:${wire.to.pinId}`;
  }

  step(components: ComponentInstance[], wires: Wire[]): SimulationResult {
    this.initNets(components, wires);

    for (const comp of components) {
      if (comp.kind === "resistor") {
        this.processResistor(comp);
      } else if (comp.kind === "led") {
        this.processLED(comp);
      } else if (comp.kind === "microcontroller") {
        this.processDigitalCore(comp);
      }
    }

    const voltages: Record<string, number> = {};
    const currents: Record<string, number> = {};
    const logic: Record<string, 0 | 1> = {};

    for (const [key, net] of this.nets.entries()) {
      voltages[key] = net.voltage;
      currents[key] = net.current;
      logic[key] = net.logic;
    }

    return {
      timestamp: Date.now(),
      voltages,
      currents,
      logic
    };
  }

  private processResistor(comp: ComponentInstance) {
    const resistance = Number(comp.properties?.resistance ?? 1000);
    const [a, b] = comp.pins;
    const netA = a.net ?? `${comp.id}:${a.id}`;
    const netB = b.net ?? `${comp.id}:${b.id}`;
    const vA = this.nets.get(netA)?.voltage ?? 0;
    const vB = this.nets.get(netB)?.voltage ?? 0;
    const current = (vA - vB) / resistance;
    this.nets.set(netA, { voltage: vA, current, logic: vA > 2.5 ? 1 : 0 });
    this.nets.set(netB, { voltage: vB, current: -current, logic: vB > 2.5 ? 1 : 0 });
  }

  private processLED(comp: ComponentInstance) {
    const forwardVoltage = Number(comp.properties?.vf ?? 2);
    const [anode, cathode] = comp.pins;
    const netA = anode.net ?? `${comp.id}:${anode.id}`;
    const netC = cathode.net ?? `${comp.id}:${cathode.id}`;
    const vA = this.nets.get(netA)?.voltage ?? 0;
    const vC = this.nets.get(netC)?.voltage ?? 0;
    const on = vA - vC >= forwardVoltage;
    this.nets.set(netA, { voltage: vA, current: on ? 0.01 : 0, logic: on ? 1 : 0 });
    this.nets.set(netC, { voltage: vC, current: on ? -0.01 : 0, logic: on ? 0 : 0 });
  }

  private processDigitalCore(comp: ComponentInstance) {
    const state = comp.properties?.logicState as Record<string, 0 | 1> | undefined;
    for (const pin of comp.pins) {
      const netKey = pin.net ?? `${comp.id}:${pin.id}`;
      const target = state?.[pin.id] ?? 0;
      this.nets.set(netKey, {
        voltage: target ? this.supplyVoltage : 0,
        current: 0,
        logic: target
      });
    }
  }
}
