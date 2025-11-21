# API image
FROM node:20-alpine AS base
WORKDIR /app

# Copier uniquement l'API pour un build rapide
COPY ./apps/api/package.json ./apps/api/tsconfig.json ./tsconfig.base.json ./
RUN npm install
COPY ./apps/api ./apps/api
RUN npm run build --prefix ./apps/api

FROM node:20-alpine
WORKDIR /app
COPY --from=base /app/apps/api/dist ./dist
COPY --from=base /app/node_modules ./node_modules
ENV PORT=4000
EXPOSE 4000
CMD ["node", "dist/server.js"]
