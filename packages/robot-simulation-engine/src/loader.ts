import { URDFLoader } from "three-urdf-loader";
import * as THREE from "three";

export type RobotCatalogEntry = {
  name: string;
  vendor: string;
  urdfPath: string;
  meshesPath?: string;
  dof: number;
};

export type LoadedRobotModel = {
  id: string;
  entry: RobotCatalogEntry;
  scene: THREE.Group;
};

async function loadCatalog(): Promise<Record<string, RobotCatalogEntry>> {
  if (typeof window !== "undefined") {
    const res = await fetch("/robots/robotCatalog.json");
    if (!res.ok) throw new Error("robotCatalog.json introuvable");
    return (await res.json()) as Record<string, RobotCatalogEntry>;
  }
  const fs = await import("fs");
  const path = await import("path");
  const catalogPath = path.resolve(process.cwd(), "robots/robotCatalog.json");
  return JSON.parse(fs.readFileSync(catalogPath, "utf-8"));
}

export async function loadRobotModel(robotId: string): Promise<LoadedRobotModel> {
  const catalog = await loadCatalog();
  const entry = catalog[robotId];
  if (!entry) throw new Error(`Robot ${robotId} absent du catalogue`);

  const loader = new URDFLoader();
  if (entry.meshesPath) {
    loader.packages = {
      ".": entry.meshesPath
    };
  }

  const basePath =
    typeof window !== "undefined"
      ? `${entry.urdfPath.startsWith("/") ? "" : "/"}${entry.urdfPath}`
      : entry.urdfPath;

  return new Promise((resolve, reject) => {
    loader.load(
      basePath,
      (urdf) => {
        resolve({
          id: robotId,
          entry,
          scene: urdf
        });
      },
      undefined,
      (err) => reject(err)
    );
  });
}
