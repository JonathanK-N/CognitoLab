import type { ComponentInstance, Wire } from "../types";

const colors: Record<string, string> = {
  led: "#f97316",
  resistor: "#6366f1",
  capacitor: "#0ea5e9",
  microcontroller: "#0f172a",
  sensor: "#22c55e",
  actuator: "#14b8a6",
  wire: "#1e40af"
};

export class CanvasRenderer {
  private ctx: CanvasRenderingContext2D | null = null;

  constructor(private canvas: HTMLCanvasElement) {
    this.ctx = canvas.getContext("2d");
    this.resize();
  }

  resize() {
    const ratio = window.devicePixelRatio || 1;
    this.canvas.width = this.canvas.clientWidth * ratio;
    this.canvas.height = this.canvas.clientHeight * ratio;
    this.ctx?.scale(ratio, ratio);
  }

  render(components: ComponentInstance[], wires: Wire[]) {
    if (!this.ctx) return;
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    ctx.save();
    ctx.strokeStyle = "#94a3b8";
    ctx.lineWidth = 1.5;
    ctx.setLineDash([5, 5]);
    for (let x = 0; x < this.canvas.width; x += 25) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, this.canvas.height);
      ctx.stroke();
    }
    for (let y = 0; y < this.canvas.height; y += 25) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(this.canvas.width, y);
      ctx.stroke();
    }
    ctx.restore();

    wires.forEach((wire) => {
      ctx.strokeStyle = wire.color ?? "#0f172a";
      ctx.lineWidth = 3;
      ctx.beginPath();
      const from = components.find((c) => c.id === wire.from.componentId);
      const to = components.find((c) => c.id === wire.to.componentId);
      if (!from || !to) return;
      ctx.moveTo(from.position.x, from.position.y);
      ctx.lineTo(to.position.x, to.position.y);
      ctx.stroke();
    });

    for (const comp of components) {
      ctx.save();
      ctx.translate(comp.position.x, comp.position.y);
      if (comp.rotation) ctx.rotate((comp.rotation * Math.PI) / 180);
      ctx.fillStyle = colors[comp.kind] ?? "#1f2937";
      ctx.strokeStyle = "rgba(15,23,42,0.4)";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.roundRect(-20, -12, 40, 24, 6);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = "white";
      ctx.font = "10px Inter, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(comp.name, 0, 3);
      ctx.restore();
    }
  }
}
