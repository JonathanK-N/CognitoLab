export type JointSnapshot = {
  timestamp: number;
  joints: number[];
};

export class RobotRecorder {
  private frames: JointSnapshot[] = [];
  private startTime: number | null = null;

  start() {
    this.frames = [];
    this.startTime = performance.now();
  }

  capture(joints: number[]) {
    if (this.startTime === null) this.start();
    this.frames.push({ timestamp: performance.now() - (this.startTime ?? 0), joints });
  }

  stop() {
    this.startTime = null;
  }

  exportJSON() {
    return JSON.stringify({ frames: this.frames }, null, 2);
  }

  importJSON(json: string) {
    const parsed = JSON.parse(json);
    this.frames = parsed.frames ?? [];
  }

  playback(speed = 1, onFrame: (frame: JointSnapshot) => void) {
    for (const frame of this.frames) {
      setTimeout(() => onFrame(frame), frame.timestamp / speed);
    }
  }
}
