import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { loadRobotModel, LoadedRobotModel } from "./loader";

export type Robot3DSimulatorProps = {
  robotId: string;
  mode?: "studio" | "atelier";
  height?: number;
  onLoaded?: (model: LoadedRobotModel) => void;
};

export const Robot3DSimulator: React.FC<Robot3DSimulatorProps> = ({
  robotId,
  mode = "studio",
  height = 520,
  onLoaded
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!canvasRef.current) return;
    let mounted = true;
    const renderer = new THREE.WebGLRenderer({ canvas: canvasRef.current, antialias: true });
    renderer.setSize(canvasRef.current.clientWidth, height);
    renderer.setPixelRatio(window.devicePixelRatio || 1);
    renderer.shadowMap.enabled = true;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(mode === "studio" ? "#0f172a" : "#111827");
    const grid = new THREE.GridHelper(12, 24, 0x4b5563, 0x1f2937);
    const floor = new THREE.Mesh(
      new THREE.PlaneGeometry(20, 20),
      new THREE.MeshStandardMaterial({
        color: mode === "studio" ? "#111827" : "#0f172a",
        roughness: 0.8,
        metalness: 0.2
      })
    );
    floor.rotation.x = -Math.PI / 2;
    floor.receiveShadow = true;
    scene.add(grid);
    scene.add(floor);

    const camera = new THREE.PerspectiveCamera(50, canvasRef.current.clientWidth / height, 0.1, 100);
    camera.position.set(4, 4, 6);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(0, 1, 0);
    controls.update();

    const ambient = new THREE.AmbientLight(0xffffff, 0.5);
    const dir = new THREE.DirectionalLight(0xffffff, 1.1);
    dir.position.set(2, 6, 4);
    dir.castShadow = true;
    dir.shadow.mapSize.set(2048, 2048);
    scene.add(ambient, dir);

    loadRobotModel(robotId)
      .then((res) => {
        if (!mounted) return;
        res.scene.traverse((obj: any) => {
          if (obj.isMesh) {
            obj.castShadow = true;
            obj.receiveShadow = true;
          }
        });
        res.scene.position.set(0, 0, 0);
        scene.add(res.scene);
        onLoaded?.(res);
      })
      .catch((err) => setError(err.message));

    const animate = () => {
      if (!mounted) return;
      controls.update();
      renderer.render(scene, camera);
      requestAnimationFrame(animate);
    };
    animate();

    const onResize = () => {
      if (!canvasRef.current) return;
      const w = canvasRef.current.clientWidth;
      camera.aspect = w / height;
      camera.updateProjectionMatrix();
      renderer.setSize(w, height);
    };
    window.addEventListener("resize", onResize);

    return () => {
      mounted = false;
      window.removeEventListener("resize", onResize);
      renderer.dispose();
      scene.clear();
    };
  }, [robotId, mode, height, onLoaded]);

  return (
    <div className="relative w-full" style={{ height }}>
      <canvas ref={canvasRef} className="w-full h-full rounded-lg overflow-hidden" />
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/60 text-white">
          Erreur de chargement : {error}
        </div>
      )}
    </div>
  );
};
