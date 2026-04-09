# ── Stage 1: Build ────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder
WORKDIR /monorepo

COPY package.json ./
COPY apps/api/package.json            ./apps/api/
COPY apps/web/package.json            ./apps/web/
COPY apps/mobile/package.json         ./apps/mobile/
COPY packages/ui/package.json                            ./packages/ui/
COPY packages/simulator-core/package.json                ./packages/simulator-core/
COPY packages/robot-simulation-engine/package.json       ./packages/robot-simulation-engine/
COPY packages/libraries/components-svg/package.json      ./packages/libraries/components-svg/

RUN npm install

COPY apps/mobile  ./apps/mobile
COPY packages/ui  ./packages/ui
COPY tsconfig.base.json ./

RUN npm run build --prefix apps/mobile

# ── Stage 2: Serve ─────────────────────────────────────────────────────────────
FROM node:20-alpine
RUN npm install -g serve

COPY --from=builder /monorepo/apps/mobile/dist /app/dist

EXPOSE 3000
CMD ["sh", "-c", "serve -s /app/dist -l ${PORT:-3000}"]
