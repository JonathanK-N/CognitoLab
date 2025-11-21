# Web (Vite) image
FROM node:20-alpine AS builder
WORKDIR /app
# deps monorepo
COPY package.json package-lock.json* turbo.json tsconfig.base.json ./
COPY apps/web/package.json apps/web/tsconfig.json apps/web/tailwind.config.cjs apps/web/postcss.config.cjs ./apps/web/
RUN npm install
COPY . .
RUN npm run build --prefix apps/web

FROM nginx:1.25-alpine
COPY --from=builder /app/apps/web/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
