import * as THREE from "three";
import { inverseKinematicsCCD, DHParam, interpolateTrajectory } from "./kinematics";

export type PickPlaceTask = {
  pick: { x: number; y: number; z: number };
  place: { x: number; y: number; z: number };
  speed?: number;
};

export function planPickPlace(params: DHParam[], task: PickPlaceTask) {
  const waypoints = [
    inverseKinematicsCCD(params, { position: new THREE.Vector3(task.pick.x, task.pick.y, task.pick.z) }),
    inverseKinematicsCCD(params, { position: new THREE.Vector3(task.place.x, task.place.y, task.place.z) })
  ];
  return interpolateTrajectory(waypoints, 20);
}

export function detectCollision(robotMeshes: THREE.Object3D[], obstacles: THREE.Object3D[]): boolean {
  const robotBoxes = robotMeshes.map((m) => new THREE.Box3().setFromObject(m));
  const obstacleBoxes = obstacles.map((m) => new THREE.Box3().setFromObject(m));
  return robotBoxes.some((rb) => obstacleBoxes.some((ob) => rb.intersectsBox(ob)));
}
