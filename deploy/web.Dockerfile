# Web (Vite) image
FROM node:20-alpine AS builder
WORKDIR /app
COPY ./apps/web/package.json ./apps/web/tsconfig.json ./apps/web/tailwind.config.cjs ./apps/web/postcss.config.cjs ./tsconfig.base.json ./
RUN npm install
COPY ./packages ./packages
COPY ./apps/web ./apps/web
RUN npm run build --prefix ./apps/web

FROM nginx:1.25-alpine
COPY --from=builder /app/apps/web/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
