import { SimulationEngine } from "./logic/engine";
import { CanvasRenderer } from "./graphics/canvasRenderer";
import type {
  ComponentInstance,
  SimulationOptions,
  SimulationResult,
  Wire
} from "./types";

export class CircuitSimulator {
  private components: Map<string, ComponentInstance> = new Map();
  private wires: Map<string, Wire> = new Map();
  private engine: SimulationEngine;
  private renderer?: CanvasRenderer;

  constructor(private options: SimulationOptions = {}) {
    this.engine = new SimulationEngine(options);
  }

  attachRenderer(canvas: HTMLCanvasElement) {
    this.renderer = new CanvasRenderer(canvas);
    this.renderer.render([...this.components.values()], [...this.wires.values()]);
  }

  addComponent(component: ComponentInstance) {
    this.components.set(component.id, component);
    this.renderer?.render([...this.components.values()], [...this.wires.values()]);
  }

  updateComponent(component: ComponentInstance) {
    this.components.set(component.id, component);
    this.renderer?.render([...this.components.values()], [...this.wires.values()]);
  }

  removeComponent(componentId: string) {
    this.components.delete(componentId);
    this.renderer?.render([...this.components.values()], [...this.wires.values()]);
  }

  addWire(wire: Wire) {
    this.wires.set(wire.id, wire);
    this.renderer?.render([...this.components.values()], [...this.wires.values()]);
  }

  getState() {
    return {
      components: [...this.components.values()],
      wires: [...this.wires.values()]
    };
  }

  step(): SimulationResult {
    return this.engine.step([...this.components.values()], [...this.wires.values()]);
  }
}
