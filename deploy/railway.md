# Déploiement Railway

1. Créer deux services Railway : `api` (Node) et `web` (Static).
2. API :
   - Build command : `npm install && npm run build --prefix apps/api`
   - Start command : `node dist/server.js`
   - Variables : `MONGO_URL` (Railway Mongo), `JWT_SECRET`.
3. Web :
   - Build command : `npm install && npm run build --prefix apps/web`
   - Start command : `npx serve -s apps/web/dist -l 4173`
4. Ajouter un service MongoDB managé.
5. Exposer le port 4173 pour le front, 4000 pour l’API.
