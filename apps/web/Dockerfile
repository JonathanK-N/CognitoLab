# ── Stage 1: Build ────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder
WORKDIR /monorepo

# Copy workspace manifests first (Docker layer cache)
COPY package.json ./
COPY apps/api/package.json            ./apps/api/
COPY apps/web/package.json            ./apps/web/
COPY apps/mobile/package.json         ./apps/mobile/
COPY packages/ui/package.json                            ./packages/ui/
COPY packages/simulator-core/package.json                ./packages/simulator-core/
COPY packages/robot-simulation-engine/package.json       ./packages/robot-simulation-engine/
COPY packages/libraries/components-svg/package.json      ./packages/libraries/components-svg/

# Install all workspace deps from root (resolves workspace:*)
RUN npm install

# Copy all source needed for the web build
COPY apps/web             ./apps/web
COPY apps/api/package.json ./apps/api/package.json
COPY packages             ./packages
COPY robots               ./robots
COPY tsconfig.base.json   ./

# Build Vite app
RUN npm run build --prefix apps/web

# ── Stage 2: Serve ─────────────────────────────────────────────────────────────
FROM node:20-alpine
RUN npm install -g serve

COPY --from=builder /monorepo/apps/web/dist /app/dist

EXPOSE 3000
CMD ["sh", "-c", "serve -s /app/dist -l ${PORT:-3000}"]
