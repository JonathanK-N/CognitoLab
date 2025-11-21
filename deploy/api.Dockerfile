# API image
FROM node:20-alpine AS base
WORKDIR /app
# deps du monorepo (turborepo/workspaces)
COPY package.json package-lock.json* turbo.json tsconfig.base.json ./
COPY apps/api/package.json apps/api/tsconfig.json ./apps/api/
RUN npm install
COPY . .
RUN npm run build --prefix apps/api

FROM node:20-alpine
WORKDIR /app
ENV PORT=4000
COPY --from=base /app/apps/api/dist ./dist
COPY --from=base /app/node_modules ./node_modules
CMD ["node", "dist/server.js"]
