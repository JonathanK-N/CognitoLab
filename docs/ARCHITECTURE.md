# Architecture CognitoLab

- Monorepo Turbo (apps/web, apps/api, apps/mobile, packages/ui, packages/simulator-core, packages/robot-simulation-engine, packages/libraries/components-svg, robots).
- Frontend : React + Vite + TS + Tailwind + Zustand + React Router (PWA ready). Simulateur Wokwi (iframe), Renode WASM placeholder, simulateur interne canvas/WebGL.
- Backend : Express + MongoDB + JWT + rôles (admin/professeur/etudiant/invite/utilisateur) + WebSocket `/ws/simulation`.
- Robotique : module `@cognitolab/robot-simulation-engine` (Three.js, URDF loader, IK CCD, trajectoires, enregistreur), catalogue `robots/robotCatalog.json`, script `scripts/fetch_urdf_models.sh`.
- Icônes : `packages/libraries/components-svg/icons/*.svg` + script `generate-png.js` pour PNG 1024×1024.
- Déploiement : Dockerfiles web/api, docker-compose, instructions Railway (`deploy/railway.md`).
