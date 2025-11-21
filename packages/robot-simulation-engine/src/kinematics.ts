import * as THREE from "three";

export type DHParam = {
  a: number;
  alpha: number;
  d: number;
  theta: number;
};

export type JointState = {
  theta: number[];
};

export type Pose = {
  position: THREE.Vector3;
  quaternion: THREE.Quaternion;
};

export function dhMatrix({ a, alpha, d, theta }: DHParam): THREE.Matrix4 {
  const ca = Math.cos(alpha);
  const sa = Math.sin(alpha);
  const ct = Math.cos(theta);
  const st = Math.sin(theta);
  return new THREE.Matrix4().set(
    ct,
    -st * ca,
    st * sa,
    a * ct,
    st,
    ct * ca,
    -ct * sa,
    a * st,
    0,
    sa,
    ca,
    d,
    0,
    0,
    0,
    1
  );
}

export function forwardKinematics(params: DHParam[]): Pose {
  const transform = params.reduce((acc, p) => acc.multiply(dhMatrix(p)), new THREE.Matrix4());
  const position = new THREE.Vector3().setFromMatrixPosition(transform);
  const quaternion = new THREE.Quaternion().setFromRotationMatrix(transform);
  return { position, quaternion };
}

export type IKTarget = { position: THREE.Vector3; quaternion?: THREE.Quaternion };

export function inverseKinematicsCCD(
  params: DHParam[],
  target: IKTarget,
  iterations = 50,
  step = 0.15
): JointState {
  const joints = params.map((p) => p.theta);
  for (let iter = 0; iter < iterations; iter++) {
    for (let i = params.length - 1; i >= 0; i--) {
      const fk = forwardKinematics(
        params.map((p, idx) => ({
          ...p,
          theta: joints[idx]
        }))
      );
      const end = fk.position;
      const jointPos = forwardKinematics(
        params.slice(0, i).map((p, idx) => ({ ...p, theta: joints[idx] }))
      ).position;
      const toEnd = end.clone().sub(jointPos);
      const toTarget = target.position.clone().sub(jointPos);
      const angle = toEnd.angleTo(toTarget);
      const axis = toEnd.clone().cross(toTarget).normalize();
      if (isNaN(angle) || axis.length() === 0) continue;
      const delta = Math.min(angle, step);
      joints[i] += delta * Math.sign(axis.z || 1);
    }
  }
  return { theta: joints };
}

export function interpolateTrajectory(
  waypoints: JointState[],
  stepsPerSegment = 10
): JointState[] {
  const result: JointState[] = [];
  for (let i = 0; i < waypoints.length - 1; i++) {
    const from = waypoints[i].theta;
    const to = waypoints[i + 1].theta;
    for (let s = 0; s <= stepsPerSegment; s++) {
      const t = s / stepsPerSegment;
      result.push({
        theta: from.map((v, idx) => v + (to[idx] - v) * t)
      });
    }
  }
  return result;
}
